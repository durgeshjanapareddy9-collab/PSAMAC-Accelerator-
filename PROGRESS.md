# PROGRESS: AxMAC

Status key: [ ] todo · [~] in progress · [x] done (check passed and output shown)

Update this file at the end of every session: tick the boxes and add a line to the session
log. If you fall behind, cut the CNN evaluation first. Keep the baseline comparison.

## Milestone 1: due Thu Oct 1, 2026

**Day 1: Sat Sep 26**
- [x] M1.1 Set up the environment and record tool versions; create the repo and Makefile skeleton; copy REFERENCES.md into docs/; first commit
- [x] M1.2 Flow smoke test: synthesize mul_behav (a*b) to sky130_fd_sc_hd and print its area
- [x] M1.3 Python model, LUT and pytest tests: the closed-form MED check, plus N=4 giving EDmax 49 occurring for 256 pairs

**Day 2: Sun Sep 27**
- [x] M1.4 Write gen_dadda.py, generate rtl/dadda8_reduce.sv, and add the full/half adders
- [x] M1.5 Build approx_mul.sv with the N mask; the exhaustive testbench passes for N=0 (65,536/65,536)

**Day 3: Mon Sep 28**
- [x] M1.6 `make test` passes for all N = 0..12
- [x] M1.7 metrics.py: MED, NMED, MRED, ER, ME, and EDmax with its frequency, written to a CSV and plotted
- [ ] M1.8 (optional) Functional cross-check against TruMD at N = 2, 4, 6, 8 (skipped for now to reach M1.13)

**Day 4: Tue Sep 29**
- [x] M1.9 Build mul_wrap; run Yosys and OpenSTA to get area and delay for N=0 and for a*b
- [x] M1.10 Power for N=0: simulation VCD, then OpenSTA report_power (random stimulus, documented)

**Day 5: Wed Sep 30**
- [x] M1.11 (if time) Area and delay for every N, written to results/ppa_mul.csv
- [x] M1.12 Write the README and docs/milestone1.md
- [~] M1.13 Clean-clone check (`make test metrics synth power` works), then push to Git (clean-clone check passed, results byte-identical; push waiting for a GitHub remote)

**What we submit on Oct 1** (contents of docs/milestone1.md):
1. Repo link, containing the RTL, testbenches, model and scripts.
2. A description of the multiplier and the N knob.
3. The verification result: RTL matches the model on all 65,536 inputs for N = 0..12.
4. The error-metrics table and plot (MED, NMED, MRED, ER, and max error with its frequency).
5. Area, delay and power for the exact N=0 design, compared against a*b.
6. The plan for Milestone 2.

## Milestone 2: due Thu Oct 29, 2026

**Week 1 (Oct 2-8): MAC, array and first image results**
- [ ] M2.1 mac_pe.sv and its testbench (bit-exact against the LUT golden model)
- [ ] M2.2 New 4x4 systolic_array.sv, built from scratch, and its testbench (random matrices; all tested N pass)
- [ ] M2.3 image_conv.py: PSNR and SSIM across our N sweep (software only), including the Rather et al. cameraman case (Gaussian noise with variance 0.01, 3x3 averaging)

**Week 2 (Oct 9-15): PPA sweep and baselines**
- [ ] M2.4 Realistic image stimulus, and the power flow working with it
- [ ] M2.5 Area, delay and power vs N for the multiplier and the array (results/ppa_*.csv)
- [ ] M2.6 Fetch 3-4 EvoApproxLib designs and TruMD; verify each against its own model; build their LUTs. Optional: add a functional-only reconstruction of Rather et al. Design 1 (N=4 +12)
- [ ] M2.7 Run the baselines through the identical flow (results/ppa_baselines.csv)

**Week 3 (Oct 16-22): Application accuracy and analysis**
- [ ] M2.8 Image evaluation for every design: our N points plus the baselines
- [ ] M2.9 CNN: train on MNIST, quantize, run LUT-based inference, and get top-1 accuracy for every design
- [ ] M2.10 analysis.py: test the Rather et al. observation of which metric (mean error, or EDmax and its frequency) best predicts quality loss
- [ ] M2.11 An image patch run through the RTL array matches the Python model

**Week 4 (Oct 23-28): Figures, report and release**
- [ ] M2.12 Figures:
  - error vs N;
  - area, delay and power vs N;
  - PSNR and SSIM vs N;
  - top-1 accuracy vs N;
  - accuracy vs area/delay/power curves (with the baselines marked);
  - the metric-correlation chart.
- [ ] M2.13 docs/report.md: motivation, design, verification, results, baselines, analysis, limitations, prior work (cited from docs/REFERENCES.md), and a comparison with Rather et al.
- [ ] M2.14 `make all` in a clean clone reproduces every figure; final README; tag v1.0
- [ ] M2.15 (optional) LibreLane layout for N=0 and one approximate N

**What we submit on Oct 29:**
1. Repo (tagged v1.0), with a README that reproduces every figure from scratch.
2. The final report, including:
   - the accuracy-vs-area/delay/power curves;
   - image PSNR/SSIM;
   - the CNN top-1 accuracy change;
   - the baseline comparison;
   - the error-metric analysis.
3. Slides, if the course asks for them.

## After the course (not due Oct 29)
- [ ] A1 Add a second approximation family (partial-product perforation, or Mitchell logarithmic)
- [ ] A2 Integrate the multiplier into the RV32IM core, with CSR-controlled exact/approximate mode
- [ ] A3 Spike co-simulation showing that exact mode is bit-accurate

## Team
| Area | Owner |
|---|---|
| Flow (Yosys/OpenSTA/power) and baselines | |
| RTL and testbenches | |
| Python model, metrics, image evaluation, CNN | |
| Report and README | everyone |

## Session log
<!-- One line per session: date · who · what was done · checks run · next step · blockers -->
2026-09-27 · Durgesh + Claude · M1.1-M1.12 done (OpenSTA 3.1.0 built from source; Yosys 0.33; sky130A tt corner) · make test 13/13 N PASS, 42 pytest pass, gate-level power sim 2008/2008 correct, clean clone reproduces results byte-identical · next: push to GitHub (M1.13), then M2.1 · open: ABC delay non-monotonic in N (decide timing-driven mapping for M2.5); CLAUDE.local.md not committed (team decision)
