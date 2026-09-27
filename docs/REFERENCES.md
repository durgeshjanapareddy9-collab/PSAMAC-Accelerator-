# References: AxMAC

This file lists every source the project uses. It lives in docs/ and is committed, since
the report needs a bibliography anyway.

Rules:
- Cite from this list.
- Before adding a new source, check that it exists and that you have read it.
- Check each repo's license before copying any code, and credit the repo in the README.

## Key reference
1. A. A. Rather, B. Khurshid, S. A. Banday, A. A. Algarni, "Design of high-performance,
   accurate, and approximate Dadda-tree multipliers for image processing applications,"
   *Scientific Reports* 15, 41338 (2025). doi:10.1038/s41598-025-25239-2.
   Open access: https://www.nature.com/articles/s41598-025-25239-2
   - FPGA precision scaling of an 8x8 Dadda multiplier.
   - Observes that image quality tracks EDmax and how often it occurs.
   - Licensed CC BY-NC-ND: cite it and describe it, but do not copy or adapt its figures.

## Closest related work
2. H. Afzali-Kusha, M. Vaeztourshizi, M. Kamal, M. Pedram, "Design exploration of
   energy-efficient accuracy-configurable Dadda multipliers with improved lifetime based on
   voltage overscaling," *IEEE TVLSI* 28(5), 1207–1220 (2020).
   doi:10.1109/TVLSI.2020.2978874. This is X-Dadda; the TruMD repo asks for this citation.
3. D. Vungarala et al., "TPU-Gen: LLM-driven custom tensor processing unit generator,"
   arXiv:2503.05951 (2025). https://arxiv.org/pdf/2503.05951
   Code: https://github.com/ACADLab/TPU_Gen
4. M. E. Elbtity et al., "APTPU: Approximate computing based tensor processing unit,"
   *IEEE TCAS-I* 69, 5135–5146 (2022).

## Multiplier fundamentals and truncation
5. L. Dadda, "Some schemes for parallel multipliers," *Alta Frequenza* 34, 349–356 (1965).
6. C. S. Wallace, "A suggestion for a fast multiplier," *IEEE Trans. Electronic Computers*
   EC-13(1) (1964).
7. M. J. Schulte, E. E. Swartzlander, "Truncated multiplication with correction constant,"
   *VLSI Signal Processing VI*, 388–396 (1993). doi:10.1109/VLSISP.1993.404467
8. "Leveraging highly approximated multipliers in DNN inference," arXiv:2412.16757 (2024).
   https://arxiv.org/pdf/2412.16757
   Gives the formula for a truncated multiplier, which our Python model follows.

## Error metrics and surveys
9. J. Liang, J. Han, F. Lombardi, "New metrics for the reliability of approximate and
   probabilistic adders," *IEEE Trans. Computers* 62(9), 1760–1771 (2013).
   doi:10.1109/TC.2012.146. Defines ED, MED and related metrics.
10. H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate arithmetic circuits:
    A survey, characterization, and recent applications," *Proc. IEEE* 108(12) (2020).
    doi:10.1109/JPROC.2020.3006451.
    PDF: https://www.researchgate.net/publication/343617252
11. H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A review, classification and
    comparative evaluation of approximate arithmetic circuits," *ACM JETC* 13(4) (2017).
    doi:10.1145/3094124

## Approximate circuit libraries (baselines)
12. V. Mrazek, R. Hrbacek, Z. Vasicek, L. Sekanina, "EvoApprox8b: Library of approximate
    adders and multipliers for circuit design and benchmarking of approximation methods,"
    *DATE* 2017, 258–261. doi:10.23919/DATE.2017.7926993
13. V. Mrazek, L. Sekanina, Z. Vasicek, "Libraries of approximate circuits: Automated
    design and application in CNN accelerators," *IEEE JETCAS* 10(4), 406–418 (2020).
    doi:10.1109/JETCAS.2020.3032495.
    Free PDF: https://fit.vut.cz/research/publication-file/c168178/280392/libraries_of_Approximate_Circuits.pdf
14. V. Mrazek, Z. Vasicek, L. Sekanina, H. Jiang, J. Han, "Scalable construction of
    approximate multipliers with formally guaranteed worst case error," *IEEE TVLSI*
    26(11) (2018).

## Accelerators
15. N. P. Jouppi et al., "In-datacenter performance analysis of a tensor processing unit,"
    *ISCA* 2017. https://arxiv.org/abs/1704.04760

## CNN and image evaluation
16. D. Danopoulos et al., "AdaPT: Fast emulation of approximate DNN accelerators in
    PyTorch," *IEEE TCAD* (2022). https://arxiv.org/abs/2203.04071
    Code: https://github.com/dimdano/adapt
17. F. Vaverka, V. Mrazek, Z. Vasicek, L. Sekanina, "TFApprox: Towards a fast emulation
    of DNN approximate hardware accelerators on GPU," *DATE* 2020, 294–297.
    Code: https://github.com/ehw-fit/tf-approximate
18. Z. Wang, A. C. Bovik, H. R. Sheikh, E. P. Simoncelli, "Image quality assessment: from
    error visibility to structural similarity," *IEEE TIP* 13(4), 600–612 (2004). (SSIM)
19. B. Jacob et al., "Quantization and training of neural networks for efficient
    integer-arithmetic-only inference," *CVPR* 2018. (int8 quantization)
20. Y. LeCun, L. Bottou, Y. Bengio, P. Haffner, "Gradient-based learning applied to
    document recognition," *Proc. IEEE* 86(11) (1998). (LeNet, MNIST)

## Tools (cite in the report's methodology section)
21. M. Shalan, T. Edwards, "Building OpenLANE: A 130nm OpenROAD-based tapeout-proven
    flow," *ICCAD* 2020. LibreLane asks users to cite this paper.
22. Yosys, OpenSTA/OpenROAD and the SkyWater SKY130 PDK. Cite them by name and version,
    using the versions recorded in results/tool_versions.txt.

## Code and repos we use or learn from
- EvoApproxLib: https://github.com/ehw-fit/evoapproxlib (site: https://ehw.fit.vutbr.cz/evoapproxlib/)
- EvoApprox8b: https://github.com/ehw-fit/evoapprox8b
- TruMD and other 8-bit approximate multipliers: https://github.com/Hassan313/Approximate-Multiplier
- MulApprox: https://github.com/RatkoFri/MulApprox
- Exact Dadda reference RTL: https://github.com/tharunchitipolu/Dadda-Multiplier-using-CSA
- Systolic array on sky130 (LibreLane): https://github.com/Harshit-12Kaundal/systolic-array-matmul-asic
- Systolic array testbench pattern (cocotb + numpy): https://github.com/deaneeth/tiny-tpu
- Systolic array with skew buffers: https://github.com/ebube-ic/systolic-tensor-core-verilog
- LUT-based CNN emulation: https://github.com/woshimark666/ApproxTorch
- Approximate multipliers on sky130 via OpenLane (blog): https://endraws.com/posts/tinytapeout-08/

## Toolchain docs
- IIC-OSIC-TOOLS Docker image: https://github.com/iic-jku/IIC-OSIC-TOOLS
- LibreLane: https://github.com/librelane/librelane
- LibreLane PDK notes: https://librelane.readthedocs.io/en/latest/usage/about_pdks.html
- Power estimation with SAIF in OpenROAD: https://antmicro.com/blog/2025/07/power-estimation-in-openroad-using-saif-in-verilator
