import os
import time
import subprocess
import json
import requests

# Configurations
GCP_PROJECT = "g24ai1067-vcc-assignment"
GCP_ZONE = "us-central1-a"
INSTANCE_GROUP = "web-migration"
LOCAL_APP_PATH = "~/app/app.py"
REMOTE_APP_PATH = "~/app/app.py"
CPU_THRESHOLD = 75  # CPU threshold to trigger migration
PROMETHEUS_URL = "http://localhost:9090/api/v1/query"

def get_cpu_usage():
    """Returns the current CPU usage percentage from Prometheus."""
    try:
        query = "100 - (avg by(instance) (rate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)"
        response = requests.get(PROMETHEUS_URL, params={"query": query})
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("data", {}).get("result", [])
            if result:
                cpu_value = float(result[0]["value"][1])
                return round(cpu_value, 2)
            else:
                print("No CPU data received from Prometheus.")
        else:
            print(f"Prometheus API Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error fetching CPU usage: {e}")
    
    return 0

def trigger_gcp_scaling():
    """Triggers GCP auto-scaling to create a new instance."""
    print("High CPU detected! Scaling to GCP...")
    command = (
        f"gcloud compute instance-groups managed resize {INSTANCE_GROUP} --size=2 "
        f"--zone={GCP_ZONE} --project={GCP_PROJECT}"
    )
    os.system(command)

def get_new_instance():
    """Finds the most recently created instance in the managed instance group."""
    try:
        result = subprocess.check_output(
            f"gcloud compute instance-groups managed list-instances {INSTANCE_GROUP} "
            f"--zone={GCP_ZONE} --project={GCP_PROJECT} --format=json",
            shell=True,
        ).decode()

        instances = json.loads(result)
        running_instances = [i for i in instances if i["instanceStatus"] == "RUNNING"]
        
        if not running_instances:
            print("No running instances found. Waiting...")
            time.sleep(5)
            return None

        return running_instances[0]["instance"].split("/")[-1]  # Extract instance name

    except Exception as e:
        print(f"Error fetching instances: {e}")
        return None

def deploy_to_gcp(instance_name):
    """Deploys the Flask app to the given GCP instance."""
    print(f"Deploying app to {instance_name}...")

    commands = [
        f"gcloud compute ssh {instance_name} --zone={GCP_ZONE} --command='mkdir -p ~/app'",

        f"gcloud compute scp {LOCAL_APP_PATH} {instance_name}:{REMOTE_APP_PATH} --zone={GCP_ZONE}",

        f"gcloud compute ssh {instance_name} --zone={GCP_ZONE} "
        f"--command='sudo apt update && sudo apt install -y python3-pip && pip3 install flask && "
        f"nohup python3 ~/app/app.py > ~/app/log.txt 2>&1 &'"
    ]

    for cmd in commands:
        os.system(cmd)

    print(f"Application deployed successfully on {instance_name}")

def main():
    """Main script execution."""
    cpu_usage = get_cpu_usage()
    print(f"Current CPU Usage: {cpu_usage}%")

    if cpu_usage > CPU_THRESHOLD:
        trigger_gcp_scaling()
        time.sleep(10)  # Give GCP time to create the instance

        instance_name = None
        while not instance_name:
            instance_name = get_new_instance()
            time.sleep(5)

        deploy_to_gcp(instance_name)
        print("Migration completed.")

    else:
        print("CPU usage is normal. No action required.")

if __name__ == "__main__":
    main()
