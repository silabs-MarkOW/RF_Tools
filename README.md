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

## Python Script
```
usage: analyze.py [-h] --iq IQ --f-sample F_SAMPLE [--amp AMP] [--phase PHASE]
                  [--sine] [--fft] [--left LEFT] [--right RIGHT]
                  [--preamble PREAMBLE] [--N N]
analyze.py: error: the following arguments are required: --iq, --f-sample
```

Currently can display frequency spectra of selected region or decoding of Bluetooth 1M PHY.

Work flow:  Initially plots amplitude of entire file.  Selecting a region (zoom) will pass the range selected to the next stage when graph is closed.  After selecting range in amplitude view, range is plotted as modulation, with darkness of point corresponding to amplitude. After modulation graph is closed, either spectra is plotted (`--FFT`) or default is to decode as 1M PHY.  In decode mode, additional modulation graph is displayed, a symmetric selection of preamble should be selected (for example if 10101010 is preamble, select from peak of first 1 to bottom of last 0.  This region us used to sync start of symbols.
