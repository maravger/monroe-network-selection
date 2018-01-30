# Overview

In UNIQUE, we aspire to evolve, implement and experiment with a unified utility-based framework based on both QoS (network-centric) and QoE (user-centric) features and parameters, which allows to enhance, formulate and improve various advanced network operations in mobile broadband (MBB) infrastructures (network selection, offloading, resource allocation, etc.).  

In this software extension, the operation and benefit of the proposed utility-based framework, in a utility-based access network selection application is implemented. The framework is used to evaluate the combined QoE-QoS quality of an MBB interface and determine the more superior. This can be further used for key user-desired and bandwidth intensive network services and applications, such as multimedia downloading.

## Experiment template
A template to show of some of the capabilities of this software module.

The experiment will constantly communicate with a public iperf server in
order to evaluate the condition (e.g. jitter, transmission rate, packet loss)
of the routes selected by each of the node's available interfaces. 

A utility function will be applied to the metrics collected ("metrics vector"), 
and the preferable interface will be selected based on a total score.

Accumulated in this total score will be a QoE value derived from a pre-compiled
matrix containing the QoE values corresponding to some metrics vectors (QoS). 
These values have been collected off-line from real-world experimenters.

The off-line metrics vector scoring the minimum euclidean distance with the on-line
metrics vector, will give the corresponding QoE value.
 
The default values for the weights used in the utility function are 
(can be overridden by providing a config file):
```
{
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

```
The download will abort when either size OR time OR actual size of the "url" is
downloaded.

## The experiment will execute a statement similar to running iperf like this
```bash
iperf3 -c 91.138.176.151 -p 5001 -u -R -t 2 -J
```

## Sample output
The experiment will produce an output similar to this:
```
op0 at 2018-01-30 14:21:16.966311:
bytes: 294912
bits_per_second: 1179340.25218
jitter_ms: 24.280589
lost_percent: 26.315789
out_of_order: 0
packets: 19
lost_packets: 5
seconds: 2.000522
utility: 2.07118880123
qoe: 1.0
total utility: 3.07118880123

op1 at 2018-01-30 14:21:20.854210: 
bytes: 294912
bits_per_second: 1179296.54224
jitter_ms: 30.680238
lost_percent: 11.111111
out_of_order: 0
packets: 18
lost_packets: 2
seconds: 2.000596
utility: 2.21612198035
qoe: 3.0
total utility: 5.21612198035
--------------------------------------------------
Preferable interface: op1
--------------------------------------------------

```
