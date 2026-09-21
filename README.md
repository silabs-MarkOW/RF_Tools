# RF Tools

Humble beginings as tool to process IQdata sampled from HackRF One.  Hoping it can be applied to Rohde&Schwarz which appears to be a powerful device, but accessible through toy applications.

Example HackRF usage:
```
hackrf_transfer -f 2404000000 -s 20000000 -b 15000000 -r 2404cstest-0x0401-20MHz.iq -n 2000000
```

* `-f 2404000000` RF frequency 2404 MHz
* `-s 20000000` Sampling frequency 20MHz
* `-b 15000000` Bandwidth 15 MHz
* `-r 2404cstest-0x0401-20MHz.iq`
* `-n 2000000` 2 Msamples thus 100 ms

