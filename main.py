import subprocess
import yaml
from tabulate import tabulate
import re
import pprint as pp
import json
from py_k8s_aggregation.aggregation import PodNodeInstanceTypeAggregator
from mde.mde_eleases import releases as mde_releases


def run_command(command):
    #print(f"Executing command: \n {command}")
    result = subprocess.run(command, text=True, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        raise RuntimeError(f"Error executing command: {result.stderr.strip()}")



def get_namepased_releases(namespace:str):
    command = f" helm ls -n {namespace} -o json | jq -r '.[].name'"
    releases_lines = run_command(command)
    return list(map(lambda x: x.strip(), releases_lines.split('\n')))# Split the data into lines and clean newline characters ('\n')


'''
DOD :
Agrregate all services in the givem teams.
View the following data :
[Service (Release) name | node type | Max replicas | Memory | CPU] 
'''

def main():
    aggregator = PodNodeInstanceTypeAggregator()
    table_data = []
    counter = 0
    try:
        for namespace in mde_teams_ns:
            aggregator.set_namespace(namespace)
            print(f"namespace : {namespace}")

            for release in mde_releases[namespace]:

                command = f" helm get values {release} -n {namespace} -o json"
                valus_json = run_command(command)
                values_dict = json.loads(valus_json)

                # Node instance type
                node_type = None
                if 'tolerations' not in values_dict and 'nodeSelector' not in values_dict:
                    # Agrigate node type by schedual pods.
                    instance_type = aggregator.get_pods_instance_types(release)
                    node_type = dict(instance_type)
                    # print(instance_type)
                else: 
                    if 'tolerations' in values_dict:
                        # print(values_dict['tolerations'][0].get('value'))
                        node_type = values_dict['tolerations'][0].get('value')
                    if 'nodeSelector' in values_dict:
                        node_selector_sku = None 
                        if "beta.kubernetes.io/instance-type" in values_dict['nodeSelector']:
                            node_type = values_dict['nodeSelector']["beta.kubernetes.io/instance-type"]
                        else:
                            node_type = values_dict['nodeSelector']["node.kubernetes.io/instance-type"]

                # Max replicas
                keda = values_dict.get('keda', {})
                max_replicas = keda.get('maxReplicaCount')
                if max_replicas == None:
                    hpa = values_dict.get('hpa', {})
                    max_replicas = hpa.get('maxReplicas', {})

                # CPU & Memory    
                resources = values_dict.get('resources', {})
                requests = resources.get('requests', {})
                memory =  requests.get('memory')
                cpu = requests.get('cpu')

                # Nodes Consumption
                # By Memort 
                memory_node_count = max_replicas * 
                # By CPU 
                cpu_node_count = 

                # Create a row for the table
                table_row = [
                    release,
                    node_type,
                    max_replicas,
                    memory,
                    cpu,
                ]

                table_data.append(table_row)

            # Define the table headers
            headers = [
                "Service (Release) name",
                "Node type",
                "Max replicas",
                "Memory",
                "CPU",
            ]

            col_alignments = ["right"] * 5
            print(tabulate(table_data, headers, tablefmt="pretty", stralign=col_alignments))
            table_data = []

    except Exception as e:
        print("An error occurred:", str(e))

if __name__ == "__main__":
    main()