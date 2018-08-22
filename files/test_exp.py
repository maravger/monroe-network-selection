#!/usr/bin/python

import json
import sys
import netifaces
import subprocess
import math
import datetime
import csv

CONFIG = {
	"zmqport": "tcp://172.17.0.1:5556"
	}

# Configuration File
CONFIGFILE = '/opt/mavgeris/config'
QOSQOE = 'https://www.dropbox.com/s/6mtlssomfwnqd3m/QoS-QoE-table-UNIQUE_oper4_tcp.csv'
# CONFIGFILE = 'https://www.dropbox.com/s/rk54woyfl439dur/config'

# Default Values
EXPCONFIG = {
        "w1": 1,
        "w2": 1,
        "w3": 1,
        "w4": 1,
        "w5": 1,
        "w6": 1,
        "w7": 0.01,
        "c1": 1000000,
        "c2": 1,
        "c3": 1,
        "c4": 0.01,
        "c5": 0.01,
        "c6": 1,
        "c7": 1,
        "plossmax": 100,
        "jittermax": 300
        }

def main():
    
    # Create qoeqos table
    subprocess.call(["wget", "-q", QOSQOE, "-O", "/opt/mavgeris/qoe-qos-table-temp.csv"])
    try:
        with open('/opt/mavgeris/qoe-qos-table-temp.csv', 'rb') as f:
            reader = csv.reader(f)
            with open('/opt/mavgeris/qoe-qos-table.csv', 'wb') as result:
                wtr= csv.writer( result )
                for r in reader:
                    wtr.writerow((r[0], r[1], r[2], r[3]))
        with open('/opt/mavgeris/qoe-qos-table.csv', 'rb') as f:
            reader = csv.reader(f)
            qoeqos = list(reader)
            column_headers = qoeqos.pop(0) # remove column headers
            qoeqos = [map(float, row) for row in qoeqos] # make every element a float
            qoe = [row.pop(0) for row in qoeqos] # only qoe
            qos = qoeqos # now containing only qos
            maxs = [max([row[i] for row in qoeqos]) for i in range(0,len(column_headers)-1)] # collect max values for every qos metric
            qos = [[row[i]/maxs[i] for i in range (0,len(column_headers)-1)] for row in qos] # normalize qos values
    except Exception as e:
            print "Cannot retrieve qoe-qos reference table  {}".format(e)
        
    # with open('/monroe/results/results.txt', 'a') as f:
    #    f.write(str(qoe))
    #    f.write('\n')
    #    f.write(str(maxs))
    #    f.write('\n')
    #    f.write(str(qos))
    #    f.write('\n\n')
 
    while True:
        subprocess.call(["wget", "-q", "https://www.dropbox.com/s/rk54woyfl439dur/config", "-O", "/opt/mavgeris/config"])
        try:
            with open(CONFIGFILE) as configfd:
                EXPCONFIG.update(json.load(configfd))
        except Exception as e:
            print "Cannot retrieve expconfig {}".format(e)

        selected_if = collect_stats(qos, qoe, maxs)
        with open('/monroe/results/results.txt', 'a') as f:
            f.write("Preferable interface: " + selected_if + "\n")
            f.write("w1 = " + str(EXPCONFIG['w1']) + "\n")
            f.write("--------------------*using tcp metrics*------------------------------\n\n")

# Helper functions
def collect_stats(qos, qoe, maxs):
    # Check availability of interfaces of interest
    if check_if('op0'):
        ipaddr0 = str(netifaces.ifaddresses('op0')[netifaces.AF_INET][0]['addr']) # ip of interface op0
        try:
            output0 = subprocess.check_output(["iperf3", "-c", "62.38.249.51", "-R", "-B", ipaddr0, "-J", "-p", "5201", "-t", "2"])
            jout0 = json.loads(output0) # parse json output into dict
            # collect actual interface stats
            with open('/monroe/results/results.txt', 'a') as f:
                end0 = jout0['end']['streams'][0]['sender']['end']
                f.write('op0 at ' + str(datetime.datetime.utcnow()) + ":\n")
                bytes0 = jout0['end']['streams'][0]['sender']['bytes']
                f.write("bytes: " + str(bytes0) + "\n")
                bps0 = jout0['end']['streams'][0]['sender']['bits_per_second']         
                f.write("bits_per_second: " + str(bps0) + "\n")
                retransmits0 = jout0['end']['streams'][0]['sender']['retransmits']
                f.write("retransmits: " + str(retransmits0) + "\n")   
                sec0 = jout0['end']['streams'][0]['udp']['seconds']
                f.write("seconds: " + str(sec0) + "\n")   
                u0 = utility_calculation(bps0, retransmits0)
                f.write("utility: " + str(u0) + "\n") 
                qoe0 = qoe_calculation(qos, qoe, maxs, [bps0, retransmits0])
                f.write("qoe: " + str(qoe0) + "\n")
                total_utility0 = u0 + qoe0
                f.write("total utility: " + str(total_utility0) + "\n\n")
        except subprocess.CalledProcessError, e:          
            with open('/monroe/results/results.txt', 'a') as f:
                f.write("!!! iperf-related error !!!\n")
                f.write("interface's IP: " + str(ipaddr0) + "\n")
                f.write("node's available interfaces: " + str(netifaces.interfaces())) 
                u0 = 0
                f.write("utility: " + str(u0) + "\n") 
                qoe0 = 0
                f.write("qoe: " + str(qoe0) + "\n") 
                total_utility0 = 0
                f.write("total utility: " + str(total_utility0) + "\n\n") 
    else:
        with open('/monroe/results/results.txt', 'a') as f:
            f.write('!!! op0 is unavailable !!!' + '\n')
            u0 = 0
            f.write("utility: " + str(u0) + "\n") 
            qoe0 = 0
            f.write("qoe: " + str(qoe0) + "\n") 
            total_utility0 = 0
            f.write("total utility: " + str(total_utility0) + "\n\n") 

    if check_if('op1'):
        ipaddr1 = str(netifaces.ifaddresses('op1')[netifaces.AF_INET][0]['addr']) # ip of interface op1
        try:
            output1 = subprocess.check_output(["iperf3", "-c", "62.38.249.51", "-R", "-B", ipaddr1, "-J", "-p", "5201", "-t", "2"])
            jout1 = json.loads(output1) # parse json output into dict
            # collect actual interface stats
            with open('/monroe/results/results.txt', 'a') as f:  
                end1 = jout1['end']['streams'][0]['sender']['end']
                f.write('op1 at ' + str(datetime.datetime.utcnow()) + ": \n")
                bytes1 = jout1['end']['streams'][0]['sender']['bytes']
                f.write("bytes: " + str(bytes1) + "\n")
                bps1 = jout1['end']['streams'][0]['sender']['bits_per_second']
                f.write("bits_per_second: " + str(bps1) + "\n")
                retransmits1 = jout1['end']['streams'][0]['sender']['retransmits']
                f.write("retransmits: " + str(retransmits1) + "\n")   
                sec1 = jout1['end']['streams'][0]['udp']['seconds']
                f.write("seconds: " + str(sec1) + "\n")   
                u1 = utility_calculation(bps1, retransmits1)
                f.write("utility: " + str(u1) + "\n")
                qoe1 = qoe_calculation(qos, qoe, maxs, [bps1, retransmits1])
                f.write("qoe: " + str(qoe1) + "\n")
                total_utility1 = u1 + qoe1
                f.write("total utility: " + str(total_utility1) + "\n")
                f.write("--------------------------------------------------\n")
        except subprocess.CalledProcessError, e:          
            with open('/monroe/results/results.txt', 'a') as f:
                f.write("!!! iperf-related error !!!\n")
                f.write("interface's IP: " + str(ipaddr0) + "\n")
                f.write("node's available interfaces: " + str(netifaces.interfaces())) 
                u1 = 0
                f.write("utility: " + str(u1) + "\n") 
                qoe1 = 0
                f.write("qoe: " + str(qoe1) + "\n") 
                total_utility1 = 0
                f.write("total utility: " + str(total_utility1) + "\n") 
                f.write("--------------------------------------------------\n")
    else:
        with open('/monroe/results/results.txt', 'a') as f:
            f.write('!!! op1 is unavailable !!!' + '\n')
            u1 = 0
            f.write("utility: " + str(u1) + "\n") 
            qoe1 = 0
            f.write("qoe: " + str(qoe1) + "\n") 
            total_utility1 = 0
            f.write("total utility: " + str(total_utility1) + "\n") 
            f.write("--------------------------------------------------\n")

    return 'op0' if total_utility0 > total_utility1 else 'op1'

def check_if(ifname):
    """Check if interface is up and have got an IP address."""
    return (ifname in netifaces.interfaces() and
            netifaces.AF_INET in netifaces.ifaddresses(ifname))

def utility_calculation(rate, retransmits):
    w1 = EXPCONFIG['w1']
    w7 = EXPCONFIG['w7']
    c1 = EXPCONFIG['c1']
    u = w1*((rate/c1)**2)/(1+((rate/c1)**2)) + w7*retransmits
    return u

def qoe_calculation(tr_qos, tr_qoe, maxs, iperf_res):
    norm_res = [iperf_res[i]/maxs[i] for i in range(0,len(iperf_res))] # normalize iperf results
    # list containing euclidean distances between iperf_results and trained data
    dist = [math.sqrt(sum([(a - b)**2 for a, b in zip(norm_res, row)])) for row in tr_qos] 
    # select the qoe corresponding to the qos vector with the minimum euclidean distance from the iperf_results
    qoe = tr_qoe[dist.index(min(dist))]
    # with open('/monroe/results/results.txt', 'a') as f:
    #   f.write(str(norm_res))
    #   f.write('\n')
    #   f.write(str(dist))
    #   f.write('\n')
    #   f.write(str(qoe))
    #   f.write('\n\n')
    return qoe

if __name__ == "__main__":
    main()
