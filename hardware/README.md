# Hardware

Hardware assets for the Xiaohui anime-pet robot prototype.

## Contents

- `bom.md`: bill of materials and major modules.
- SolidWorks files: mechanical prototype parts and assemblies.
- `概念图.jpg`: early concept image.

## Runtime Hardware Path

The current runtime hardware control is implemented in the Open-LLM-VTuber backend:

- PCA9685 shared manager
- face tracking servo service
- ear motion service

OpenClaw does not directly drive hardware.
