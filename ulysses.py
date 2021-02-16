#!/usr/bin/env python3

import argparse
import iperf3
import sys
import time
import math
import subprocess
import csv
from datetime import datetime
import pytz
import os.path
from multiprocessing import Process, Queue
from termcolor import colored

def single_test(queue, srv_address, port, duration, verbose):
    client = iperf3.Client()
    client.protocol = 'udp'
    client.server_hostname = srv_address
    client.port = port
    client.duration = duration
    # target bandwidth in bits/sec
    client.bandwidth = 1000000 # default value for UDP is 1 Mbit/s
    client.blksize = 1448 # to avoid warning for MSS 1448 - adjust value accordingly

    print('Connecting to {0}:{1}'.format(client.server_hostname, client.port))
    result = client.run()
    
    if verbose:
        if result.error:
            print(result.error)
        else:
            print('')
            if srv_address == '192.168.5.2':
                print('Test completed: PATH 1')
                path = '1'
            else:
        print('Test completed: PATH 2')
                path = '2'
            print('  started at         {0}'.format(result.time))
            print('  bytes transmitted  {0}'.format(result.bytes))
            print('  jitter (ms)        {0} (@path {1})'.format(result.jitter_ms, path))
            if (result.lost_percent < 2):
                print(colored('  loss percentage    {0}% (@path {1})\n'.format(result.lost_percent, path), 'green'))
            elif(result.lost_percent < 5):
                print(colored('  loss percentage    {0}% (@path {1})\n'.format(result.lost_percent, path), 'yellow'))
            else:
                print(colored('  loss percentage    {0}% (@path {1})\n'.format(result.lost_percent, path), 'red'))


            #print('Average transmitted data in all sorts of networky formats:')
            #print('  bits per second      (bps)   {0}'.format(result.bps))
            #print('  Kilobits per second  (kbps)  {0}'.format(result.kbps))
            #print('  Megabits per second  (Mbps)  {0}'.format(result.Mbps))
            #print('  KiloBytes per second (kB/s)  {0}'.format(result.kB_s))
            #print('  MegaBytes per second (MB/s)  {0}'.format(result.MB_s)) 
    
    if srv_address == '192.168.5.2': # path1
        queue.put(('path1', result.lost_percent, result.jitter_ms) if not result.error else None)
    else: # path2
        queue.put(('path2', result.lost_percent, result.jitter_ms) if not result.error else None)
        
    # return (result.lost_percent, result.jitter_ms) if not result.error else None


def utility_calculation(ploss, jitter):
    w4 = 0.9
    w5 = 0.1
    u = (w4 * 1.0 * ploss / 100) + (w5 * 1.0 * jitter / 0.05)
    return u


def main(timestamp):
    queue = Queue() # for communications among processes
    
    while(True):
        flag = 0
        try:
            p1 = Process(target=single_test, args=(queue, '192.168.5.2', 5201, 7, True))
            p2 = Process(target=single_test, args=(queue, '192.168.4.3', 5201, 7, True))
            p1.start()
            p2.start()
            p1.join()
            p2.join()
        except KeyboardInterrupt:
            return
        except:
            print('Test(s) failed. Repeating...')
            # flush queue
            while not queue.empty():
                queue.get() 
            continue
       
        for _ in range(2):
            res = queue.get()
            if not res: # error
                # flush queue
                while not queue.empty():
                    queue.get()
                flag = 1 # raise flag
                break # exit for
            elif res[0] == 'path1':
                l1 = res[1]
                j1 = res[2]
            else:
                l2 = res[1]
                j2 = res[2]
        
        # if there was an error continue
        if flag:
           print("Empty test - Trying again") 
           continue
        #print("path1:", l1, j1)
        #print("path2:", l2, j2)
        path1u = utility_calculation(l1, j1)
        path2u = utility_calculation(l2, j2)
        print(colored('Path 1 utility score: ' + str(path1u), 'magenta'))
        print(colored('Path 2 utility score: ' + str(path2u), 'magenta'))

        # write to csv
        devnull = open(os.devnull, 'w')
        fname = 'results' + timestamp + '.csv'
        tz_Athens = pytz.timezone('Europe/Athens')
        datetime_Athens = datetime.now(tz_Athens)
        if (path1u > path2u):
            chosen_path = 2
        else:
            chosen_path = 1
        file_exists = os.path.isfile(fname)    
        with open(fname, mode='a') as results:
            headers = ['TOD', 'ploss1', 'jitter1', 'ploss2', 'jitter2', 'path1u', 'path2', 'chosen_path']
            results_writer = csv.writer(results, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            if not file_exists:
                results_writer.writerow(headers)  # file doesn't exist yet, write a header

            results_writer.writerow([datetime_Athens.strftime("%H:%M:%S"), l1, j1, l2, j2, path1u, path2u, chosen_path])
        try:
            subprocess.call(['sudo', 'ip', 'route', 'del', '192.168.100.0/24', 'via', '192.168.3.2', 'dev', 'enp9s0f0'],stdout=devnull, stderr=subprocess.STDOUT)
            subprocess.call(['sudo', 'ip', 'route', 'del', '192.168.100.0/24', 'via', '192.168.6.1', 'dev', 'enp7s0f1'],stdout=devnull, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            pass
        if (path1u > path2u):
            # choose path 2
            print(colored("Changing to path2", 'cyan'))
            try:
                subprocess.call(['sudo', 'ip', 'route', 'add', '192.168.100.0/24', 'via', '192.168.6.1', 'dev', 'enp7s0f1'],stdout=devnull, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                pass
        else:
            # choose path 1
            print(colored("Changing to path1", 'cyan'))
            try:
                subprocess.call(['sudo', 'ip', 'route', 'add', '192.168.100.0/24', 'via', '192.168.3.2', 'dev', 'enp9s0f0'],stdout=devnull, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                pass
        print('\n ---------------------------------- \n')
        time.sleep(2)
            

if __name__ == "__main__":
    tz_Athens = pytz.timezone('Europe/Athens')
    datetime_Athens = datetime.now(tz_Athens)
    timestamp = datetime_Athens.strftime("%Y_%m_%d-%H_%M_%S_")
    main(timestamp)