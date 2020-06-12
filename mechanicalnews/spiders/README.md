# Library of spiders

The `spiders` directory contain Scrapy spiders you can use to scrape each site.

## Swedish news sites

File                     |  Spider name*             | Domain
:----------------------- | :----------------------- | :-------------
[`aftonbladet.py`](aftonbladet.py) | `aftonbladet` | aftonbladet.se
[`arbetet.py`](arbetet.py) | `arbetet` | arbetet.se
[`dagensarbete.py`](dagensarbete.py) | `dagensarbete` | da.se
[`dagensindustri.py`](dagensindustri.py) | `dagensindustri` | di.se
[`dagensnyheter.py`](dagensnyheter.py) | `dagensnyheter` | dn.se
[`etc.py`](etc.py) | `etc` | etc.se
[`expressen.py`](expressen.py) | `expressen` | expressen.se
[`feministisktperspektiv.py`](feministisktperspektiv.py) | `feministisktperspektiv` | feministisktperspektiv.se
[`friatider.py`](friatider.py) | `friatider` | friatider.se
[`goteborgsposten.py`](goteborgsposten.py) | `goteborgsposten` | gp.se
[`nyatider.py`](nyatider.py) | `nyatider` | nyatider.nu
[`nyheteridag.py`](nyheteridag.py) | `nyheteridag` | nyheteridag.se
[`samhallsnytt.py`](samhallsnytt.py) | `samhallsnytt` | samnytt.se
[`samtiden.py`](samtiden.py) | `samtiden` | samtiden.nu
[`svenskadagbladet.py`](svenskadagbladet.py) | `svenskadagbladet` | svd.se
[`sverigesradio.py`](sverigesradio.py) | `sverigesradio` | sverigesradio.se
[`sverigestelevision.py`](sverigestelevision.py) | `sverigestelevision` | svt.se
[`sydsvenskan.py`](sydsvenskan.py) | `sydsvenskan` | sydsvenskan.se
[`vlt.py`](vlt.py) | `vlt` | vlt.se

<small>\* The spider name is found in the variable `name` of each spider class. For consistency, the file name should be the same as the spider name.</small>

Start the spider using ordinary Scrapy commands (e.g., `scrapy crawl vlt`).

## Develop your own spider

See the documentation on how you can [contribute with your own spider](../../CONTRIBUTE.md).

You can then submit your spider to this library.