#!/usr/bin/env python

"""
This script automates the setup of a TeamCity project and integrates it with a Kubernetes cloud profile 
and build executor. It:

- Verifies if the specified TeamCity project exists; if not, it creates it.
- Creates a Kubernetes cloud profile and associates it with the project.
- Sets up a build executor for Kubernetes within the project.

The script reads API tokens either from a provided file path or from environment variables. 
It uses Kubernetes service account credentials (token and CA cert) for setting up the Kubernetes cloud profile.
Avoids duplicate creation of connectors or executors if they already exist.
"""

import os
import json
import base64
import urllib.request
import urllib.error
import ssl
import argparse

TEAMCITY_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def read_k8s_token_and_cacert(token_path, cacert_path):
    with open(token_path, 'r') as f:
        token = f.read().strip()
    with open(cacert_path, 'rb') as f:
        cacert = base64.b64encode(f.read()).decode('utf-8')
    return token, cacert

def make_request(url, method="GET", data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read(), response.status
    except urllib.error.HTTPError as e:
        return e.read(), e.code

def get_project_id(teamcity_url, project_name, headers):
    url = f"{teamcity_url}/app/rest/projects"
    resp, status = make_request(url, headers=headers)
    if status != 200:
        raise RuntimeError(f"Failed to retrieve projects, status {status}")

    projects = json.loads(resp.decode())
    for project in projects.get("project", []):
        if project["name"] == project_name:
            return project["id"]
    return None

def project_exists(teamcity_url, project_name, headers):
    project_id = get_project_id(teamcity_url, project_name, headers)
    return project_id is not None

def create_project(teamcity_url, project_name, headers):
    url = f"{teamcity_url}/app/rest/projects"
    payload = {
        "parentProject": {"locator": "id:_Root"},
        "name": project_name
    }
    data = json.dumps(payload).encode()
    _, status = make_request(url, method="POST", data=data, headers=headers)
    if status not in (200, 201):
        raise RuntimeError(f"Failed to create project {project_name}, status {status}")
    print(f"Created project {project_name}")

def get_project_features(teamcity_url, project_id, headers):
    url = f"{teamcity_url}/app/rest/projects/id:{project_id}/projectFeatures"
    resp, status = make_request(url, headers=headers)
    if status != 200:
        raise RuntimeError(f"Failed to retrieve features for project {project_id}, status {status}")
    return json.loads(resp.decode())

def feature_exists(features, key_name, value, feature_type):
    for feature in features.get("projectFeature", []):
        if feature.get("type") != feature_type:
            continue
        for prop in feature.get("properties", {}).get("property", []):
            if prop.get("name") == key_name and prop.get("value") == value:
                return True
    return False

def create_k8s_connector(teamcity_url, project_id, profile, token, cacert, headers):
    """
    Create a Kubernetes connection (OAuthProvider) in TeamCity for the project.
    """
    url = f"{teamcity_url}/app/rest/projects/id:{project_id}/projectFeatures"
    payload = {
        "project": {"id": project_id},
        "name": profile["name"],
        "cloudCode": "kubernetes",
        "type": "OAuthProvider",
        "properties": {
            "property": [
                {"name": "apiServerUrl", "value": profile["apiServerUrl"]},
                {"name": "namespace", "value": profile["namespace"]},
                {"name": "displayName", "value": profile["name"]},
                {"name": "authStrategy", "value": "token"},
                {"name": "providerType", "value": "KubernetesConnection"},
                {"name": "secure:caCertData", "value": cacert},
                {"name": "secure:authToken", "value": token}
            ]
        }
    }
    data = json.dumps(payload).encode()
    resp, status = make_request(url, method="POST", data=data, headers=headers)
    if status not in (200, 201):
        raise RuntimeError(f"Failed to create Kubernetes connector, status {status}")
    result = json.loads(resp.decode())
    print(f"Created Kubernetes connector: {profile['name']}")
    return result["id"]

def update_k8s_connector(teamcity_url, project_id, connector_id, cacert, token, headers):
    # Get existing feature
    url = f"{teamcity_url}/app/rest/projects/id:{project_id}/projectFeatures/id:{connector_id}"
    resp, status = make_request(url, headers=headers)
    if status != 200:
        raise RuntimeError(f"Failed to fetch Kubernetes connector for update, status {status}")

    feature = json.loads(resp.decode())

    # Update secure properties
    props = feature.get("properties", {}).get("property", [])
    # Helper to update or add property
    def upsert_property(name, value):
        for p in props:
            if p["name"] == name:
                p["value"] = value
                return
        props.append({"name": name, "value": value})

    upsert_property("secure:caCertData", cacert)
    upsert_property("secure:authToken", token)

    feature["properties"]["property"] = props

    # PUT updated feature back
    data = json.dumps(feature).encode()
    resp, status = make_request(url, method="PUT", data=data, headers=headers)
    if status not in (200, 201):
        raise RuntimeError(f"Failed to update Kubernetes connector, status {status}, response: {resp.decode(errors='replace')}")
    print(f"Updated Kubernetes connector {connector_id} with new caCertData and authToken")


def create_k8s_cloud_profile(teamcity_url, project_id, profile, connector_id, headers):
    """
    Create a Kubernetes cloud profile (BuildExecutor) that uses the connector.
    """
    url = f"{teamcity_url}/app/rest/projects/id:{project_id}/projectFeatures"
    payload = {
        "type": "BuildExecutor",
        "properties": {
            "property": [
                {"name": "buildsLimit", "value": profile["buildsLimit"]},
                {"name": "connectionId", "value": connector_id},
                {"name": "executorType", "value": "KubernetesExecutor"},
                {"name": "profileDescription", "value": "k8s agent"},
                {"name": "profileName", "value": "k8s agent"},
                {"name": "profileServerUrl", "value": teamcity_url},
                {"name": "containerParameters", "value": profile["containerParameters"]},
                {"name": "templateName", "value": profile["templateName"]}
            ]
        }
    }
    data = json.dumps(payload).encode()
    resp, status = make_request(url, method="POST", data=data, headers=headers)
    if status not in (200, 201):
        raise RuntimeError(f"Failed to add Kubernetes cloud profile, status {status}")
    print("Created Kubernetes cloud profile")


def main():
    parser = argparse.ArgumentParser(description="TeamCity + Kubernetes bootstrap")
    parser.add_argument("--teamcity-url", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--k8s-profile-name", required=True)
    parser.add_argument("--k8s-api-server-url", required=True)
    parser.add_argument("--k8s-namespace", required=True)
    parser.add_argument("--k8s-builds-limit", required=True)
    parser.add_argument("--k8s-container-parameters", required=True)
    parser.add_argument("--k8s-template-name", required=True)
    parser.add_argument("--api-token-path", default=None)
    parser.add_argument("--token-path", default="/var/run/secrets/kubernetes.io/serviceaccount/token")
    parser.add_argument("--cacert-path", default="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
    args = parser.parse_args()

    if args.api_token_path:
        with open(args.api_token_path, 'r') as f:
            api_token = f.read().strip()
    else:
        api_token = os.getenv('API_TOKEN')
        if not api_token:
            raise RuntimeError("API token is not provided or found in environment variables.")

    token, cacert = read_k8s_token_and_cacert(args.token_path, args.cacert_path)
    headers = TEAMCITY_HEADERS.copy()
    headers["Authorization"] = f"Bearer {api_token}"

    if not project_exists(args.teamcity_url, args.project_name, headers):
        create_project(args.teamcity_url, args.project_name, headers)
    else:
        print(f"Project {args.project_name} already exists.")

    project_id = get_project_id(args.teamcity_url, args.project_name, headers)
    features = get_project_features(args.teamcity_url, project_id, headers)

    k8s_profile = {
        "name": args.k8s_profile_name,
        "apiServerUrl": args.k8s_api_server_url,
        "namespace": args.k8s_namespace,
        "buildsLimit": args.k8s_builds_limit,
        "containerParameters": args.k8s_container_parameters,
        "templateName": args.k8s_template_name
    }

    if not feature_exists(features, "displayName", k8s_profile["name"], "OAuthProvider"):
        oauth_id = create_k8s_connector(args.teamcity_url, project_id, k8s_profile, token, cacert, headers) 
    else:
        print(f"Kubernetes cloud profile {k8s_profile['name']} already exists.")
        oauth_id = next(
            f["id"] for f in features["projectFeature"]
            if f["type"] == "OAuthProvider" and
               any(p["name"] == "displayName" and p["value"] == k8s_profile["name"]
                   for p in f.get("properties", {}).get("property", []))
        )
        update_k8s_connector(args.teamcity_url, project_id, oauth_id, cacert, token, headers)
    

    if not feature_exists(features, "profileName", "k8s agent", "BuildExecutor"):
        create_k8s_cloud_profile(args.teamcity_url, project_id, k8s_profile, oauth_id, headers)
    else:
        print("BuildExecutor feature 'k8s agent' already exists.")

if __name__ == "__main__":
    main()

