{{- define "teamcity-k8s-agent.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "teamcity-k8s-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "teamcity-k8s-agent.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "teamcity-k8s-agent.labels" -}}
app.kubernetes.io/name: {{ include "teamcity-k8s-agent.name" . | quote }}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service | quote }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | quote }}
{{- end }}

{{- define "joinMap" -}}
{{- $first := true -}}
{{- range $k, $v := . -}}
  {{- if not $first }},{{ end -}}
  {{- printf "%s=%s" $k $v -}}
  {{- $first = false -}}
{{- end -}}
{{- end -}}

{{- define "teamcity-k8s-agent.name.apiToken" -}}
{{- if and .Values.teamcity.apiToken (not .Values.teamcity.existingApiTokenSecret) }}
{{- include "teamcity-k8s-agent.fullname" . }}-token
{{- else if .Values.teamcity.existingApiTokenSecret -}}
{{ .Values.teamcity.existingApiTokenSecret }}
{{- end }}
{{- end }}
