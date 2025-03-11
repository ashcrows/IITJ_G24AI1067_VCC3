# Step-by-Step Guide: Local VM Setup, Monitoring, and Auto-Scaling to GCP

## Step 1: Create a Local Fedora VM using VirtualBox

1. **Download Fedora ISO:**

   - Get the latest Fedora ISO from [Fedora's official website](https://getfedora.org/).

2. **Create a Virtual Machine in VirtualBox:**

   - Open VirtualBox and click on `New`.
   - Set Name: `LocalFedoraVM`
   - Type: `Linux`
   - Version: `Fedora (64-bit)`
   - Allocate at least **4GB RAM** and **2 CPU cores**.
   - Create a **Virtual Hard Disk (20GB or more, VDI format, dynamically allocated)**.

3. **Install Fedora:**

   - Start the VM and attach the Fedora ISO.
   - Follow the installation steps and create a user account.
   - Once installed, remove the ISO and reboot.

4. **Enable SSH Access:**

   ```bash
   sudo dnf install -y openssh-server
   sudo systemctl enable --now sshd
   ```

---

## Step 2: Install and Configure Prometheus & Grafana for Monitoring

### 2.1 Install Prometheus

```bash
sudo useradd --no-create-home --shell /bin/false prometheus
sudo mkdir /etc/prometheus /var/lib/prometheus
sudo chown prometheus:prometheus /etc/prometheus /var/lib/prometheus
```

```bash
wget https://github.com/prometheus/prometheus/releases/latest/download/prometheus-linux-amd64.tar.gz
```

```bash
sudo tar xvf prometheus-linux-amd64.tar.gz -C /usr/local/bin --strip-components=1
sudo chown prometheus:prometheus /usr/local/bin/prometheus
```

### 2.2 Configure Prometheus

```bash
sudo tee /etc/prometheus/prometheus.yml > /dev/null <<EOF
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now prometheus
```

### 2.3 Install Grafana

```bash
sudo dnf install -y grafana
sudo systemctl enable --now grafana-server
```

### 2.4 Configure Grafana to Use Prometheus as a Data Source

1. Open Grafana in a web browser: `http://localhost:3000`
2. Login with default credentials: `admin/admin`
3. Add Data Source:
   - Type: `Prometheus`
   - URL: `http://localhost:9090`
   - Save and Test.

---

## Step 3: Configure Auto-Scaling on GCP

### 3.1 Set Up GCP CLI on Fedora VM

```bash
sudo dnf install -y google-cloud-sdk
```

```bash
gcloud auth login
```

### 3.2 Create a Managed Instance Group with Debian VMs

```bash
gcloud compute instance-templates create web-template \
    --machine-type=e2-medium \
    --image-family=debian-11 \
    --image-project=debian-cloud
```

```bash
gcloud compute instance-groups webmanaged create web-mig \
    --template=web-template \
    --size=1 \
    --zone=us-central1-a
```

```bash
gcloud compute instance-groups managed set-autoscaling web-mig \
    --max-num-replicas 5 \
    --target-cpu-utilization 0.75 \
    --cool-down-period 60 \
    --zone=us-central1-a
```

---

## Step 4: Deploy a Sample Flask Application

### 4.1 Create `app.py` on Local VM

```bash
mkdir -p ~/app && cd ~/app
cat <<EOF > app.py
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "Hello from Local Fedora VM"
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF
```

```bash
pip3 install flask
python3 app.py &
```

---

## Step 5: Implement Auto-Migration to GCP

### 5.1 Create Migration Script

```bash
mkdir -p ~/migration && cd ~/migration
cat <<EOF > migration_script.py
import os
import time
import psutil
from google.cloud import compute_v1

def check_cpu_usage():
    return psutil.cpu_percent(interval=10) > 75

def trigger_instance_group():
    os.system("gcloud compute instance-groups managed resize web-mig --size=2 --zone=us-central1-a")
    print("Triggered Auto-Scaling in GCP")

def deploy_app():
    os.system("gcloud compute ssh \
              --zone=us-central1-a \
              --command='nohup python3 /home/user/app.py &' \
              $(gcloud compute instances list --format='value(name)' --filter='name~web-mig')")
    print("Application deployed on GCP VM")

while True:
    if check_cpu_usage():
        print("High CPU detected! Scaling to GCP...")
        trigger_instance_group()
        deploy_app()
        break
EOF
```

### 5.2 Execute Migration Script

```bash
python3 ~/migration/migration_script.py
```

---

## Step 6: Demonstrate Auto-Scaling

1. **Start CPU Stress Test on Local VM:**
   ```bash
   sudo dnf install -y stress
   stress --cpu 2 --timeo'
   ```
2. **Monitor Grafana Dashboard:** Verify CPU spikes.
3. **Run Migration Script:** Observe logs.
4. **Verify App in GCP:**
   ```bash
   gcloud compute instances list
   ```
   - Copy External IP of the instance and test `http://EXTERNAL_IP:5000`

---

## Step 7: Auto-Scaling Down

1. **Close Application in Cloud VM:**
   ```bash
   gcloud compute ssh \
   --zone=us-central1-a \
   --command='pkill python3' \
   $(gcloud compute instances list --format='value(name)' --filter='name~web-mig')
   ```
2. **Resize Instance Group Down:**
   ```bash
   gcloud compute instance-groups managed resize web-mig --size=1 --zone=us-central1-a
   ```

---

## Summary

- **Local Fedora VM** runs the application and monitors CPU usage.
- When **CPU exceeds 75%**, migration script triggers **auto-scaling in GCP**.
- Application is **deployed to a scaled GCP Debian VM**.
- **Auto-scale down** when the application is closed.

This ensures dynamic workload balancing between local and cloud resources.

