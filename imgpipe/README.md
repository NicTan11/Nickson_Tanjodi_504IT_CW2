# PSB504IT Coursework 2
### Nickson Tanjodi
### **Quick Start Guide**

Before we start, keep in mind that
- --workers n controls the number of processes used in parallel mode
- Best worker values to test are typically 2,4,8(and/or up to your CPU logical processors)

## Project Structure

```
imgpipe/
  .venv/
  imgpipe.py
  make_inputs.py
  summarise_timings.py
  requirements.txt
  input/              (optional: your own images)
  input_small/
  input_med/
  input_large/
  output/             (created after running)
```
  
  
**1. Prerequisites**
- Windows Powershell
- Python Installed ( python 3.14+)
- Project folder


**2. Create and activate a virtual environment**
```
cd C:\Users\ngami\PycharmProjects\Nickson_Tanjodi_504IT_CW2\imgpipe
```
- From the imgpipe folder
```Powershell
cd C:\Users\"Project Path"\imgpipe

py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked
```Powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```


**3. Install dependncies**
```Powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify if Pillow is installed correctly 
```Powershell
python -c "import PIL; print(PIL.__version__)"
```


**4. Generate test datasets (Small/ Medium/ Large)**

This project includes a dataset generator for the ease of user and reproducibility
```Powershell
python make_inputs.py --out input_small --count 120  --sizes 640x480 800x600 --format jpg
python make_inputs.py --out input_med   --count 500  --sizes 1280x720 1600x900 --format jpg
python make_inputs.py --out input_large --count 1000 --sizes 1920x1080 2560x1440 --format jpg
```
Verify counts
```Powershell
(Get-ChildItem .\input_small -File).Count
(Get-ChildItem .\input_med -File).Count
(Get-ChildItem .\input_large -File).Count
```

**5. Run the software in Sequential or Parallel**

Sequential
```Powershell
python imgpipe.py --in input_small --out output --mode seq --runs 3
python imgpipe.py --in input_med   --out output --mode seq --runs 3
python imgpipe.py --in input_large --out output --mode seq --runs 3
```

Parallel, configurable workers (parallel processes requested)
```Powershell
python imgpipe.py --in input_small --out output --mode par --workers 2 --runs 3
python imgpipe.py --in input_small --out output --mode par --workers 4 --runs 3
python imgpipe.py --in input_small --out output --mode par --workers 8 --runs 3
```
```Powershell
python imgpipe.py --in input_med --out output --mode par --workers 2 --runs 3
python imgpipe.py --in input_med --out output --mode par --workers 4 --runs 3
python imgpipe.py --in input_med --out output --mode par --workers 8 --runs 3
```
```Powershell
python imgpipe.py --in input_Large --out output --mode par --workers 2 --runs 3
python imgpipe.py --in input_large --out output --mode par --workers 4 --runs 3
python imgpipe.py --in input_large --out output --mode par --workers 8 --runs 3
```


**6. Output files produces**

After running, the outputs will be written into
* processed images + per-image metrics:
  * output/<dataset>/<mode>_w<workers>/run<run_number>/
  * includes results.csv (per-image read/process/write times and success flag)

Global timing log (all runs):
- output/timings_all.csv

Run summarise_timing.py
```Powershell
python summarise_timings.py
```
This creates summary_table.csv (Mean/ Stddev, Speedup Table) and prints a readable summary in the terminal

**7. Hardware Utilisation Check**

Open Task Manager - Performance - CPU - Logical processors
- Sequential typically keeps fewer logical processors busy
- parallel should show multiple/all(if configured) logical processors active

**How to run process ID**

This is to count and prove the unique PIDs (parallel)
```Powershell
(Import-Csv .\output\input_large\par_w8\run1\results.csv | Select-Object -ExpandProperty pid | Sort-Object -Unique).Count
```

Show how the work was split across processes
```
Import-Csv .\output\input_large\par_w8\run1\results.csv |
Group-Object pid |
Sort-Object Count -Descending |
Select-Object Name,Count
```
Sequential
```
(Import-Csv .\output\input_large\seq_w1\run1\results.csv | Select-Object -ExpandProperty pid | Sort-Object -Unique).Count
```

**8. Clean re-run**
To avoid timing duplicate when re-running benchmarks
```Powershell
Remove-Item .\output\timings_all.csv -ErrorAction SilentlyContinue
```
```Powershell
Remove-Item -Recurse -Force .\output -ErrorAction SilentlyContinue
```
