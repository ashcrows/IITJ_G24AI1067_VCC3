# Auto Scaling local VM application to GCP VM
by IITJ_G24AI1067_VCC 
Assignment 03- VCC 

Demo Video with all plyalist [Youtube Playlist](https://youtube.com/playlist?list=PL_emJs1E9aDRaryfoBXLF718Bh8lmrRGe&si=3ObGE04Xivz-Z5bO).


For steps and instruction with sample process follow file [Steps_&_instruction.md](https://github.com/ashcrows/IITJ_G24AI1067_VCC3/blob/main/Steps_%26_instruction.md) .


## Note:
- There are two migration scripts to check the CPU usage of local:
  - Run with Prometheus services
  - Run on custom python library script
- There are two application which is executed follwoing with the running and then deploying to cloud VMs from local VMs as per policy:
  - A simple script of python to show the current hostname and ip addess of the host
  - A Live webpage which will update every 30 seconds and fetch the top 10 powerful cunrrency presnet in real time.
