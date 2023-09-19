
from kubernetes import client, config
from collections import Counter


class PodNodeInstanceTypeAggregator:
    def __init__(self, namespace='default'):
        # Load Kubernetes configuration from default location
        config.load_kube_config()

        # Get the current context
        # Index 1 is the current context
        current_context = config.list_kube_config_contexts()[1]

        # Print the current context
        print(f"Current Kubernetes Context: {current_context['name']}")

        # Initialize Kubernetes API client
        self.api_instance = client.CoreV1Api()

        self._namespace = namespace

        self._namespaced_pod = None

        self.sync_namespaced_pod()

    def set_namespace(self, namespace):
        self._namespace = namespace
        self.sync_namespaced_pod()

    def sync_namespaced_pod(self):
        self._namespaced_pod = self.api_instance.list_namespaced_pod(
            self._namespace)  # kubeapi req

    def get_pods_instance_types(self, release_name_contains):
        release_instance_types = {}
        release_instance_types = Counter(release_instance_types)
        try:

            for pod in self._namespaced_pod.items:

                if release_name_contains in pod.metadata.name:
                    # Get the node name associated with the pod
                    node_name = pod.spec.node_name

                    # Get the node instance type using node name
                    node = self.api_instance.read_node(name=node_name)
                    instance_type = node.metadata.labels.get(
                        "node.kubernetes.io/instance-type", "Unknown")  # "Unknown" is a default value that will be returned if the key is not found in the dictionary.
                    # Add instance type to the dictionary
                    release_instance_types[instance_type] += 1

            return release_instance_types

        except Exception as e:
            return f"Error: {str(e)}"