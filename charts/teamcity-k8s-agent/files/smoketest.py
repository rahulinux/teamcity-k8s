#!/usr/bin/env python

"""
TeamCity Smoke Test Script

Automates creation (if needed) of a build configuration and VCS root in TeamCity,
adds a simple build step, triggers a build, and verifies success via the REST API.
If the VCS root or build step already exists, updates their Git URL and script content.
"""

import os
import json
import time
import argparse
import urllib.request
import urllib.error

def api_request(url, method="GET", headers=None, data=None):
    req = urllib.request.Request(url, method=method, headers=headers or {}, data=data)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read(), resp.status
    except urllib.error.HTTPError as e:
        return e.read(), e.code

def get_token(token_file=None):
    if token_file:
        with open(token_file) as f:
            return f.read().strip()
    token = os.environ.get("TEAMCITY_TOKEN")
    if not token:
        raise RuntimeError("TeamCity token must be set via environment variable or --token-file.")
    return token

def get_project_id_by_name(teamcity_url, project_name, headers):
    url = f"{teamcity_url}/app/rest/projects"
    body, status = api_request(url, headers=headers)
    if status != 200:
        raise Exception(f"Failed to get projects: {body.decode(errors='replace')}")
    for proj in json.loads(body).get('project', []):
        if proj['name'] == project_name:
            return proj['id']
    raise Exception(f"Project with name '{project_name}' not found.")

def find_vcs_root(teamcity_url, project_id, vcs_root_name, headers):
    url = f"{teamcity_url}/app/rest/vcs-roots?locator=project:(id:{project_id})"
    body, status = api_request(url, headers=headers)
    if status == 404:
        return None
    if status != 200:
        raise Exception(f"Failed to get vcs roots: {body.decode(errors='replace')}")
    for vcs in json.loads(body).get('vcs-root', []):
        if vcs['name'] == vcs_root_name:
            return vcs['id']
    return None

def update_vcs_root(teamcity_url, vcs_root_id, new_git_url, headers):
    url = f"{teamcity_url}/app/rest/vcs-roots/id:{vcs_root_id}"
    body, status = api_request(url, headers=headers)
    if status != 200:
        raise Exception(f"Failed to fetch VCS root for update: {body.decode(errors='replace')}")
    vcs_root = json.loads(body)
    updated = False
    for prop in vcs_root["properties"]["property"]:
        if prop["name"] == "url":
            if prop["value"] != new_git_url:
                prop["value"] = new_git_url
                updated = True
            break
    else:
        vcs_root["properties"]["property"].append({"name": "url", "value": new_git_url})
        updated = True
    if updated:
        data = json.dumps(vcs_root).encode()
        put_url = f"{teamcity_url}/app/rest/vcs-roots/id:{vcs_root_id}"
        body, status = api_request(put_url, method="PUT", headers=headers, data=data)
        if status not in (200, 201):
            raise Exception(f"Failed to update VCS root: {body.decode(errors='replace')}")
        print(f"Updated VCS root {vcs_root_id} with new Git URL.")
    else:
        print(f"VCS root {vcs_root_id} Git URL already up to date.")

def create_vcs_root(teamcity_url, project_id, vcs_root_name, git_url, headers):
    url = f"{teamcity_url}/app/rest/vcs-roots"
    payload = {
        "name": vcs_root_name,
        "vcsName": "jetbrains.git",
        "project": {"id": project_id},
        "properties": {
            "property": [
                {"name": "url", "value": git_url},
                {"name": "branch", "value": "refs/heads/master"}
            ]
        }
    }
    data = json.dumps(payload).encode()
    body, status = api_request(url, method="POST", headers=headers, data=data)
    if status not in (200, 201):
        raise Exception(f"Failed to create vcs root: {body.decode(errors='replace')}")
    print(f"Created VCS root: {vcs_root_name}")
    return json.loads(body)["id"]

def find_build_config(teamcity_url, project_id, build_config_name, headers):
    url = f"{teamcity_url}/app/rest/projects/id:{project_id}/buildTypes"
    body, status = api_request(url, headers=headers)
    if status != 200:
        raise Exception(f"Failed to get build configs: {body.decode(errors='replace')}")
    for bt in json.loads(body).get('buildType', []):
        if bt['name'] == build_config_name:
            return bt['id']
    return None

def create_build_config(teamcity_url, project_id, build_config_name, headers):
    url = f"{teamcity_url}/app/rest/buildTypes"
    payload = {
        "name": build_config_name,
        "project": {"id": project_id}
    }
    data = json.dumps(payload).encode()
    body, status = api_request(url, method="POST", headers=headers, data=data)
    if status not in (200, 201):
        raise Exception(f"Failed to create build config: {body.decode(errors='replace')}")
    print(f"Created build configuration: {build_config_name}")
    return json.loads(body)["id"]

def attach_vcs_root(teamcity_url, build_type_id, vcs_root_id, headers):
    url = f"{teamcity_url}/app/rest/buildTypes/id:{build_type_id}/vcs-root-entries"
    body, status = api_request(url, headers=headers)
    if status != 200:
        raise Exception(f"Failed to get vcs-root-entries: {body.decode(errors='replace')}")
    attached = any(entry['vcs-root']['id'] == vcs_root_id for entry in json.loads(body).get('vcs-root-entry', []))
    if not attached:
        payload = {"vcs-root": {"id": vcs_root_id}}
        data = json.dumps(payload).encode()
        body, status = api_request(url, method="POST", headers=headers, data=data)
        if status not in (200, 201):
            raise Exception(f"Failed to attach vcs root: {body.decode(errors='replace')}")
        print(f"Attached VCS root {vcs_root_id} to build config {build_type_id}")
    else:
        print(f"VCS root {vcs_root_id} already attached to build config {build_type_id}")

def add_command_step(teamcity_url, build_type_id, headers, script_content="ls -la"):
    url = f"{teamcity_url}/app/rest/buildTypes/id:{build_type_id}/steps"
    body, status = api_request(url, headers=headers)
    if status != 200:
        raise Exception(f"Failed to get build steps: {body.decode(errors='replace')}")
    steps = json.loads(body).get('step', [])
    exists = any(
        step.get('type') == 'simpleRunner' and
        any(prop['name'] == 'script.content' and prop['value'] == script_content
            for prop in step.get('properties', {}).get('property', []))
        for step in steps
    )
    if not exists:
        payload = {
            "type": "simpleRunner",
            "properties": {
                "property": [
                    {"name": "script.content", "value": script_content},
                    {"name": "use.custom.script", "value": "true"}
                ]
            }
        }
        data = json.dumps(payload).encode()
        body, status = api_request(url, method="POST", headers=headers, data=data)
        if status not in (200, 201):
            raise Exception(f"Failed to add build step: {body.decode(errors='replace')}")
        print(f"Added command step to build config {build_type_id}")
    else:
        print(f"Command step already exists in build config {build_type_id}")

def update_command_step(teamcity_url, build_type_id, headers, script_content="ls -la"):
    # Fetch the build configuration (get steps with IDs)
    url = f"{teamcity_url}/app/rest/buildTypes/id:{build_type_id}"
    body, status = api_request(url, headers=headers)
    if status != 200:
        raise Exception(f"Failed to get build steps: {body.decode(errors='replace')}")
    steps = json.loads(body).get('steps', {'step': []})

    # Only update the first simpleRunner step
    for step in steps['step']:
        if step.get('type') == 'simpleRunner':
            props = step.get('properties', {}).get('property', [])
            updated = False
            for prop in props:
                if prop['name'] == 'script.content':
                    if prop['value'] != script_content:
                        prop['value'] = script_content
                        updated = True
            if updated:
                step_id = step.get('id')
                if not step_id:
                    raise Exception("Build step has no 'id' field; cannot update.")
                # Remove 'id' from payload as TeamCity expects no 'id' in PUT
                step_payload = {k: v for k, v in step.items() if k != 'id'}
                step_data = json.dumps(step_payload).encode()
                step_url = f"{teamcity_url}/app/rest/buildTypes/id:{build_type_id}/steps/{step_id}"
                resp, put_status = api_request(step_url, method="PUT", headers=headers, data=step_data)
                if put_status not in (200, 201):
                    raise Exception(f"Failed to update build step: {resp.decode(errors='replace')}")
                print(f"Updated build step script content for build config {build_type_id}")
            else:
                print("Build step script content already up to date.")
            return

    # If you want to strictly update only, and no step found:
    raise Exception("No simpleRunner step found to update.")


def trigger_and_wait_for_build(teamcity_url, build_type_id, headers):
    trigger_url = f"{teamcity_url}/app/rest/buildQueue"
    payload = {"buildType": {"id": build_type_id}}
    data = json.dumps(payload).encode()
    body, status = api_request(trigger_url, method="POST", headers=headers, data=data)
    if status not in (200, 201):
        raise Exception(f"Failed to trigger build: {body.decode(errors='replace')}")
    build_id = json.loads(body)["id"]
    print(f"Triggered build {build_id} for build config {build_type_id}")

    build_url = f"{teamcity_url}/app/rest/builds/id:{build_id}"
    for _ in range(30):  # wait max 5 minutes
        body, status = api_request(build_url, headers=headers)
        if status != 200:
            raise Exception(f"Failed to get build status: {body.decode(errors='replace')}")
        state = json.loads(body)["state"]
        if state == "finished":
            status_ = json.loads(body)["status"]
            print(f"Build finished with status: {status_}")
            if status_ != "SUCCESS":
                raise Exception(f"Build finished with status: {status_}")
            break
        time.sleep(10)
    else:
        raise TimeoutError("Build did not finish in time")

def main():
    parser = argparse.ArgumentParser(description="TeamCity Build Config Smoke Test")
    parser.add_argument("--teamcity-url", required=True, help="TeamCity server URL")
    parser.add_argument("--project-name", required=True, help="TeamCity project name")
    parser.add_argument("--git-url", required=True, help="Git repository URL")
    parser.add_argument("--build-config-name", default="SmokeTest", help="Build configuration name")
    parser.add_argument("--vcs-root-name", default=None, help="VCS root name (default: <build-config-name>-Git)")
    parser.add_argument("--script-content", default="ls -la", help="Shell command for build step")
    parser.add_argument("--token-file", default=None, help="Path to file containing TeamCity token (optional, else use TEAMCITY_TOKEN env var)")
    args = parser.parse_args()

    token = get_token(args.token_file)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    # Resolve project ID by name
    project_id = get_project_id_by_name(args.teamcity_url, args.project_name, headers)
    vcs_root_name = args.vcs_root_name or f"{args.build_config_name}-Git"

    # VCS root: create or update
    vcs_root_id = find_vcs_root(args.teamcity_url, project_id, vcs_root_name, headers)
    if vcs_root_id:
        update_vcs_root(args.teamcity_url, vcs_root_id, args.git_url, headers)
    else:
        vcs_root_id = create_vcs_root(args.teamcity_url, project_id, vcs_root_name, args.git_url, headers)

    # Build config: create or update
    build_type_id = find_build_config(args.teamcity_url, project_id, args.build_config_name, headers)
    if not build_type_id:
        build_type_id = create_build_config(args.teamcity_url, project_id, args.build_config_name, headers)
        add_command_step(args.teamcity_url, build_type_id, headers, args.script_content)
    else:
        # always update script content
        update_command_step(args.teamcity_url, build_type_id, headers, args.script_content)

    # Attach VCS root if not already attached
    attach_vcs_root(args.teamcity_url, build_type_id, vcs_root_id, headers)

    # Trigger and wait for build
    trigger_and_wait_for_build(args.teamcity_url, build_type_id, headers)
    print("Smoke test completed successfully.")

if __name__ == "__main__":
    main()

