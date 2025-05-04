{{/*
Expand the name of the chart.
*/}}
{{- define "teamcity.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "teamcity.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "teamcity.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "teamcity.name.serviceNameMain" -}}
{{- include "teamcity.fullname" . }}-main
{{- end }}


{{- define "teamcity.name.serviceNameSecondary" -}}
{{- include "teamcity.fullname" . }}-secondary
{{- end }}

{{- define "teamcity.name.serviceNameHeadless" -}}
{{- include "teamcity.fullname" . }}-headless
{{- end }}

{{- define "teamcity.name.databaseSecret" -}}
{{- if and .Values.teamcityGlobalConfigurations.database.url (not .Values.teamcityGlobalConfigurations.database.existingDatabaseSecret) }}
{{- include "teamcity.fullname" . }}-db
{{- else if .Values.teamcityGlobalConfigurations.database.existingDatabaseSecret -}}
{{ .Values.teamcityGlobalConfigurations.database.existingDatabaseSecret }}
{{- end }}
{{- end }}


{{/*
Common labels
*/}}
{{- define "teamcity.labels" -}}
helm.sh/chart: {{ include "teamcity.chart" . }}
{{ include "teamcity.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "teamcity.labels.main" -}}
role: main
{{ include "teamcity.labels" . }}
{{- end }}

{{- define "teamcity.labels.secondary" -}}
role: secondary
{{ include "teamcity.labels" . }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "teamcity.selectorLabels" -}}
app.kubernetes.io/name: {{ include "teamcity.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "teamcity.selectorLabelsMain" -}}
{{ include "teamcity.labels.main" . }}
{{- end }}

{{- define "teamcity.selectorLabelsSecondary" -}}
{{ include "teamcity.labels.secondary" . }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "teamcity.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "teamcity.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Extra config handling
*/}}

{{- define "teamcity.startupProperties" -}}
{{ range $k, $v := .Values.teamcityGlobalConfigurations.startupProperties}}-D{{$k}}={{$v}} {{end}}
{{- end}}

{{- define "teamcity.mainURL" -}}
http://{{ include "teamcity.name.serviceNameMain" . }}.{{ .Release.Namespace }}.svc.cluster.local
{{- end }}

{{- define "teamcity.mainArgument" -}}
-Dteamcity.server.rootURL={{ include "teamcity.mainURL" . }}
{{- end }}

{{- define "teamcity.mainNodeID" -}}
-Dteamcity.server.nodeId={{ .Values.main.nodeId }}
{{- end }}

{{- define "teamcity.mainOpts" -}}
{{include "teamcity.mainArgument" .}} {{include "teamcity.mainNodeID" .}} {{.Values.teamcityGlobalConfigurations.additionalServerOpts}} {{include "teamcity.startupProperties" .}} {{if .Values.main.responsibilities}} -Dteamcity.server.responsibilities={{join "," .Values.main.responsibilities}} {{end}}
{{- end }}

