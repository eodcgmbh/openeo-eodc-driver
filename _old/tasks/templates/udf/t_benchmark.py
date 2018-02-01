template = {
  "kind": "TemplateInstance",
  "apiVersion": "template.openshift.io/v1",
  "metadata": {
    "name": "eodc-benchmark-job"
  },
  "parameters": [
    {
      "name": "JOB_NAME",
      "displayName": "Job Name",
      "description": "Name of the benchmark job",
      "value": "%s",
      "required": True
    },
    {
      "name": "GIT_URI",
      "displayName": "Git URI",
      "description": "Git source URI for application",
      "value": "%s",
      "required": True
    },
    {
      "name": "GIT_REF",
      "displayName": "Git Reference",
      "description": "Git branch/tag reference",
      "value": "%s",
      "required": True
    },
    {
      "name": "GIT_SECRET",
      "displayName": "Git Secret",
      "description": "Deployment secret for accessing GitLab",
      "value": "eodc-builder",
      "required": True
    },
    {
      "name": "MEMORY_LIMIT_MIN",
      "displayName": "Minimum Memory Limit",
      "description": "Minimum amount of memory the job can use.",
      "value": "%s",
      "required": True
    },
    {
      "name": "MEMORY_LIMIT_MAX",
      "displayName": "Maximum Memory Limit",
      "description": "Maximum amount of memory the job can use.",
      "value": "%s",
      "required": True
    },
    {
      "name": "CPU_LIMIT_MIN",
      "displayName": "Minimum Memory Limit",
      "description": "Minimum amount of memory the job can use.",
      "value": "%s",
      "required": True
    },
    {
      "name": "CPU_LIMIT_MAX",
      "displayName": "Maximum Memory Limit",
      "description": "Maximum amount of memory the job can use.",
      "value": "%s",
      "required": True
    }
  ],
  "objects": [
    {
      "kind": "ImageStream",
      "apiVersion": "v1",
      "metadata": {
        "name": "${JOB_NAME}"
      },
      "spec": {
        "dockerImageRepository": None,
        "tags": [
          {
            "name": "latest"
          }
        ]
      }
    },
    {
      "kind": "BuildConfig",
      "apiVersion": "v1",
      "metadata": {
        "name": "${JOB_NAME}"
      },
      "spec": {
        "source": {
          "type": "Git",
          "git": {
            "uri": "${GIT_URI}",
            "ref": "${GIT_REF}"
          },
          "sourceSecret": {
            "name": "${GIT_SECRET}"
          }
        },
        "strategy": {
          "dockerStrategy": {
            "dockerfilePath": "Dockerfile"
          }
        },
        "output": {
          "to": {
            "kind": "ImageStreamTag",
            "name": "${JOB_NAME}:latest"
          }
        },
        "triggers": [
          {
            "type": "ConfigChange"
          },
          {
            "type": "ImageChange",
            "imageChange": None
          }
        ]
      }
    },
    {
      "kind": "Job",
      "apiVersion": "batch/v1",
      "metadata": {
        "name": "${JOB_NAME}"
      },
      "spec": {
        "activeDeadlineSeconds": 300,
        "parallelism": 1,
        "completions": 1,
        "template": {
          "metadata": {
            "labels": {
              "name": "${JOB_NAME}"
            }
          },
          "spec": {
            "containers": [
              {
                "name": "${JOB_NAME}",
                "image": "${JOB_NAME}",
                "resources": {
                  "limits": {
                    "cpu": "${CPU_LIMIT_MAX}",
                    "memory": "${MEMORY_LIMIT_MAX}"
                  },
                  "requests": {
                    "cpu": "${CPU_LIMIT_MIN}",
                    "memory": "${MEMORY_LIMIT_MIN}"
                  }
                },
                "volumeMounts": [
                  {
                    "name": "vol-eodc",
                    "mountPath": "/eodc"
                  }
                ]
              }
            ],
            "securityContext": {
              "supplementalGroups": [
                60028,
                65534
              ]
            },
            "volumes": [
              {
                "name": "vol-eodc",
                "persistentVolumeClaim": {
                  "claimName": "pvc-eodc"
                }
              }
            ]
          }
        }
      }
    }
  ]
}