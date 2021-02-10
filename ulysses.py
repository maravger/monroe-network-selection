#!/usr/bin/env python3

import argparse
import iperf3
import sys
import time
import math
import subprocess

def single_test(srv_address, port, duration, verbose):
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
            print('Test completed:')
            print('  started at         {0}'.format(result.time))
            print('  bytes transmitted  {0}'.format(result.bytes))
            print('  jitter (ms)        {0}'.format(result.jitter_ms))
            print('  loss percentage    {0}%\n'.format(result.lost_percent))

            print('Average transmitted data in all sorts of networky formats:')
            print('  bits per second      (bps)   {0}'.format(result.bps))
            print('  Kilobits per second  (kbps)  {0}'.format(result.kbps))
            print('  Megabits per second  (Mbps)  {0}'.format(result.Mbps))
            print('  KiloBytes per second (kB/s)  {0}'.format(result.kB_s))
            print('  MegaBytes per second (MB/s)  {0}'.format(result.MB_s)) 
    
    return (result.lost_percent, result.jitter_ms) if not result.error else None

def main():
    while(True):
        try:
            path1u = utility_calculation(*single_test('192.168.5.2', 5201, 5, True))
        except KeyboardInterrupt:
            return
        except:
            print('path 1 died :(')
            continue
        try:    
            path2u = utility_calculation(*single_test('192.168.4.3', 5201, 5, True))
        except KeyboardInterrupt:
            return
        except:
            print('path2 died :(')
            continue
        time.sleep(2)
        print('Path 1 utility score: ' + str(path1u))
        print('Path 2 utility score: ' + str(path2u))
        subprocess.call(['sudo', 'ip', 'route', 'del', '19.168.0.0/24', 'via', '192.168.3.2', 'dev', 'enp9s0f0'])
        subprocess.call(['sudo', 'ip', 'route', 'del', '19.168.0.0/24', 'via', '192.168.6.1', 'dev', 'enp7s0f1'])
        if (path1u > path2u):
            # subprocess.call(['sudo', 'ip', 'route', 'add', '19.168.0.0/24', 'via', '192.168.6.1', 'dev', 'enp7s0f1'])
            pass
        else:
            # subprocess.call(['sudo', 'ip', 'route', 'add', '19.168.0.0/24', 'via', '192.168.6.1', 'dev', 'enp9s0f0'])    
            pass

def utility_calculation(ploss, jitter):
    w4 = 0.5 
    w5 = 0.5 * 400
    u = w4 * ploss + w5 * jitter
    return u

if __name__ == "__main__":
    main()