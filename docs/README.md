# Instructions

The docs section consists of an `src` directory and a rendered directory. The `src` folder contains individual markdown files that are intended to be used with [stitchmd](https://github.com/abhinav/stitchmd) in order to combine multiple md files into a larger document so that common steps are not repeated in multiple documents. Users are intended to use the documentation in `rendered` as the final output of `stitchmd` will be stored there.

Each subdirectory has a `summary.md`, which is by convention, the file which defines how markdown files should be included. 

Example usage (assuming you are in `quay_guides/docs`)

```
stitchmd -C src/VMWare/ODF/CLI/  -o 'rendered/ODF_On_VMWare.md' src/VMWare/ODF/CLI/summary.md 
```
