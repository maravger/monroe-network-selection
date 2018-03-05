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
    with open('/opt/mavgeris/qoe-qos-table.csv', 'rb') as f:
        reader = csv.reader(f)
        qoeqos = list(reader)
        column_headers = qoeqos.pop(0) # remove column headers
        qoeqos = [map(float, row) for row in qoeqos] # make every element a float
        qoe = [row.pop(0) for row in qoeqos] # only qoe
        qos = qoeqos # now containing only qos
        maxs = [max([row[i] for row in qoeqos]) for i in range(0,len(column_headers)-1)] # collect max values for every qos metric
        qos = [[row[i]/maxs[i] for i in range (0,len(column_headers)-1)] for row in qos] # normalize qos values
        
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
            print "Cannot retrive expconfig {}".format(e)

        selected_if = collect_stats(qos, qoe, maxs)
        with open('/monroe/results/results.txt', 'a') as f:
            f.write("Preferable interface: " + selected_if + "\n")
            f.write("w1 = " + str(EXPCONFIG['w1']) + "\n")
            f.write("--------------------------------------------------\n\n")

# Helper functions
def collect_stats(qos, qoe, maxs):
    # Check availability of interfaces of interest
    if check_if('op0'):
        ipaddr0 = str(netifaces.ifaddresses('op0')[netifaces.AF_INET][0]['addr']) # ip of interface op0
        try:
            output0 = subprocess.check_output(["iperf3", "-c", "91.138.176.151", "-u", "-R", "-B", ipaddr0, "-J", "-p", "5001", "-t", "2"])
            jout0 = json.loads(output0) # parse json output into dict
            # collect actual interface stats
            with open('/monroe/results/results.txt', 'a') as f:
                end0 = jout0['end']['streams'][0]['udp']['end']
                f.write('op0 at ' + str(datetime.datetime.utcnow()) + ":\n")
                bytes0 = jout0['end']['streams'][0]['udp']['bytes']
                f.write("bytes: " + str(bytes0) + "\n")
                bps0 = jout0['end']['streams'][0]['udp']['bits_per_second']         
                f.write("bits_per_second: " + str(bps0) + "\n")
                jitter0 = jout0['end']['streams'][0]['udp']['jitter_ms']
                f.write("jitter_ms: " + str(jitter0) + "\n")   
                lost_prcnt0 = jout0['end']['streams'][0]['udp']['lost_percent']     
                f.write("lost_percent: " + str(lost_prcnt0) + "\n")   
                ooo0 = jout0['end']['streams'][0]['udp']['out_of_order']
                f.write("out_of_order: " + str(ooo0) + "\n")   
                pcks0 = jout0['end']['streams'][0]['udp']['packets']
                f.write("packets: " + str(pcks0) + "\n")   
                lost_pcks0 = jout0['end']['streams'][0]['udp']['lost_packets']
                f.write("lost_packets: " + str(lost_pcks0) + "\n")   
                sec0 = jout0['end']['streams'][0]['udp']['seconds']
                f.write("seconds: " + str(sec0) + "\n")   
                u0 = utility_calculation(bps0, lost_prcnt0, jitter0, ooo0)
                f.write("utility: " + str(u0) + "\n") 
                qoe0 = qoe_calculation(qos, qoe, maxs, [bps0, lost_prcnt0/100, jitter0, ooo0])
                f.write("qoe: " + str(qoe0) + "\n")
                total_utility0 = u0 + qoe0
                f.write("total utility: " + str(total_utility0) + "\n\n")
        except subprocess.CalledProcessError, e:          
            with open('/monroe/results/results.txt', 'a') as f:
                f.write("!!! iperf-related error !!!\n")
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
            output1 = subprocess.check_output(["iperf3", "-c", "91.138.176.151", "-u", "-R", "-B", ipaddr1, "-J", "-p", "5001", "-t", "2"])
            jout1 = json.loads(output1) # parse json output into dict
            # collect actual interface stats
            with open('/monroe/results/results.txt', 'a') as f:  
                end1 = jout1['end']['streams'][0]['udp']['end']
                f.write('op1 at ' + str(datetime.datetime.utcnow()) + ": \n")
                bytes1 = jout1['end']['streams'][0]['udp']['bytes']
                f.write("bytes: " + str(bytes1) + "\n")
                bps1 = jout1['end']['streams'][0]['udp']['bits_per_second']
                f.write("bits_per_second: " + str(bps1) + "\n")
                jitter1 = jout1['end']['streams'][0]['udp']['jitter_ms']
                f.write("jitter_ms: " + str(jitter1) + "\n")   
                lost_prcnt1 = jout1['end']['streams'][0]['udp']['lost_percent']
                f.write("lost_percent: " + str(lost_prcnt1) + "\n")   
                ooo1 = jout1['end']['streams'][0]['udp']['out_of_order']
                f.write("out_of_order: " + str(ooo1) + "\n")   
                pcks1 = jout1['end']['streams'][0]['udp']['packets']
                f.write("packets: " + str(pcks1) + "\n")   
                lost_pcks1 = jout1['end']['streams'][0]['udp']['lost_packets']
                f.write("lost_packets: " + str(lost_pcks1) + "\n")   
                sec1 = jout1['end']['streams'][0]['udp']['seconds']
                f.write("seconds: " + str(sec1) + "\n")   
                u1 = utility_calculation(bps1, lost_prcnt1, jitter1, ooo1)
                f.write("utility: " + str(u1) + "\n")
                qoe1 = qoe_calculation(qos, qoe, maxs, [bps1, lost_prcnt1/100, jitter1, ooo1])
                f.write("qoe: " + str(qoe1) + "\n")
                total_utility1 = u1 + qoe1
                f.write("total utility: " + str(total_utility1) + "\n")
                f.write("--------------------------------------------------\n")
        except subprocess.CalledProcessError, e:          
            with open('/monroe/results/results.txt', 'a') as f:
                f.write("!!! iperf-related error !!!\n")
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

def utility_calculation(rate, ploss, jitter, ooop):
    w1 = EXPCONFIG['w1']
    w2 = EXPCONFIG['w2']
    w3 = EXPCONFIG['w3']
    w4 = EXPCONFIG['w4']
    w5 = EXPCONFIG['w5']
    w6 = EXPCONFIG['w6']
    w7 = EXPCONFIG['w7']
    c1 = EXPCONFIG['c1']
    c2 = EXPCONFIG['c2']
    c3 = EXPCONFIG['c3']
    c4 = EXPCONFIG['c4']
    c5 = EXPCONFIG['c5']
    c6 = EXPCONFIG['c6']
    c7 = EXPCONFIG['c7']
    plossmax = EXPCONFIG['plossmax']
    jittermax = EXPCONFIG['jittermax']
    # ploss = ploss/100 # percentage
    # jitter = jitter/100 # seconds
    # rate = rate/1000000 # Mbits/sec
    u = w1*((rate/c1)**2)/(1+((rate/c1)**2)) + w4*max((1-(math.log(1+c4*ploss,10)/math.log(1+c4*plossmax,10))),0) + \
            w5*max((1-(math.log(1+c5*jitter,10)/math.log(1+c5*jittermax,10))),0) + w7*ooop
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
