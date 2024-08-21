{{- define "my-python-app.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "my-python-app.fullname" -}}
{{ .Release.Name }}-{{ include "my-python-app.name" . }}
{{- end -}}

{{- define "my-python-app.labels" -}}
app.kubernetes.io/name: {{ include "my-python-app.name" . }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: {{ .Chart.Name }}
{{- end -}}