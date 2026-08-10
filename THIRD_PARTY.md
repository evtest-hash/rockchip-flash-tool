# Third-party components

This repository vendors prebuilt binaries produced by Rockchip. They are not
part of this project's source and are redistributed as-is.

**Unverified:** the exact upstream commit for `vendor/rkbin/` and the redistribution
license Rockchip applies to these binaries have not been confirmed. Do not treat
the "Origin" entries below as legally authoritative until that is checked.

## `vendor/upgrade_tool/` — Rockchip upgrade_tool

Command-line flashing tool. Version taken from each directory's `revision.txt`.

| Path | Version | Size | SHA-256 |
|---|---|---|---|
| `vendor/upgrade_tool/darwin/upgrade_tool` | v2.44 | 908K | `c24a53050510194f5cad65d85c749c67a5d42f7d2134eb37529b67db552d5f70` |
| `vendor/upgrade_tool/linux/upgrade_tool` | v2.44 | 2804K | `65781afe7c7633d8c72187e78c31822d79f7224a979b922369970dcbbe06a430` |
| `vendor/upgrade_tool/windows/upgrade_tool.exe` | v2.46 | 1608K | `789c509dde39206d27b2f8915a5a169ff5eafb5b21fdb2108d0709bdda9ebde0` |

## `vendor/upgrade_tool/windows/driver/` — Rockchip USB driver (rockusb)

`DriverVer = 11/09/2023, 5.13.0000.0`. Signed `.sys`/`.cat`/`.inf` for x86 and
x64, covering Windows 7 / 8 / 8.1 / 10.

## `vendor/rkbin/` — Rockchip bootloaders

Origin: <https://github.com/rockchip-linux/rkbin> (upstream commit not recorded).

| File | Size | SHA-256 |
|---|---|---|
| `px30_loader_v2.11.135.bin` | 348K | `22e2dba69a7d7166e867c55ba0eca227e9f79d64f4d7a584a217650adc9e5dd5` |
| `px3se_loader_v2.09.252.bin` | 192K | `4b62d57d15a240da3fb168c36946a849d6ac58de5ad3ae7d251fcd87dc79b4a5` |
| `px5_loader_v2.06.258.bin` | 240K | `74d922305fcc1f37221a2e79ccd797fa3d6711f45d370644d6e220c95393cd86` |
| `px5_loader_v2.06.262.bin` | 248K | `1cf19601f8774f40b4c888be57d1108987a1cef0408f13de77df505ff509c6a7` |
| `rk1808_loader_v1.06.109.bin` | 284K | `54a348d4dffa9f0378bff51da69965de157eae001cd54e9ff9a492cc942fff48` |
| `rk3032_loader_v1.11.260.bin` | 188K | `979f170f51df199790ff6ef8b950e82da8eb069661315814fdd0ca710dd856a5` |
| `rk3036_echo_loader_v1.11.236.bin` | 188K | `6bb939643f4cd25d4bd77c5445aed19f29f9ce62cf8302a5d0b083a9c4ca57bb` |
| `rk3036_loader_v1.11.257.bin` | 216K | `fd5c5a444436c7560667830c3e3615ebdc24d28b5e3067a56b23234fc5059a32` |
| `rk3126_loader_v2.09.263.bin` | 200K | `defff43ccdccabef2a9d56e40559c6058a06a61162428500ce07c1025a7808da` |
| `rk3128_loader_v2.12.263.bin` | 204K | `0eda071c01441a77821f5a2c036d2850110382a535df23914278c5470637f5fd` |
| `rk3128x_loader_v1.08.257.bin` | 200K | `f9a8d1e770bd27be95b164eaf16c3f90b00dceb5647755f9f156da5de5c42f88` |
| `rk3188_loader_v2.00.200.bin` | 196K | `2c41874afc8ea28f55b6d6a309a90ff36a7529746a9a8ddf75d2718ead3f6a42` |
| `rk322x_loader_at_v1.10.256.bin` | 208K | `c4b3e5599c3568cab0b6dcb3b6e673732c810ba19ed81d9ba69bdb96b7960925` |
| `rk322x_loader_v1.10.256.bin` | 196K | `00a7d859cea73f62dc6d16ae2972d0f4c471693dce99cf15c05d72b1ec3ee207` |
| `rk322xh_loader_v1.21.250.bin` | 180K | `df16691d78b44d754cb9f7904abb2b8386275ced8789cd23bf2b0a02a15ab5f3` |
| `rk3288_loader_v1.12.263.bin` | 208K | `bbe5f9e60a2d3418dc3b2eba0e6a2dbd9efa19392a065bef580ea196830a2c01` |
| `rk3308_loader_v2.10.143.bin` | 324K | `33e7671bab6cf63596b572a3f4d034f60a86bd2d9e8eb0eb9be339d9c7ae4c7e` |
| `rk3326_loader_aarch32_v2.11.136.bin` | 348K | `1c2ab8afadd69cce5a192282beaf80c29c843863d1a89a068226b11347299cfa` |
| `rk3326_loader_v2.11.140.bin` | 352K | `9abba7eb6aa6de7454c909fda03529925ac94c0ea3a97d61e9b44d97dbd97d0a` |
| `rk3328_loader_v1.21.250.bin` | 180K | `439564a3ba8c98478ae0524e2d8a310c64a1a606f11c9549567b69366c8f3beb` |
| `rk3358_loader_v2.11.135.bin` | 348K | `c61b4053d36017a8b81b7e495fa334640c9b338aa00b1dde6a794bc07e8df8c6` |
| `rk3366_loader_v1.00.102.bin` | 224K | `bcaa7480cb0a1f234783371883047371bec430ad73f2169f9475ec5514908428` |
| `rk3368_loader_v2.06.268.bin` | 308K | `4d7b5d16534634cf16b5522e292472be526811f9f2825d6a50966b446671af7a` |
| `rk3368h_loader_v2.06.268.bin` | 308K | `4d7b5d16534634cf16b5522e292472be526811f9f2825d6a50966b446671af7a` |
| `rk3399_loader_v1.30.130.bin` | 448K | `f02e5dca398a96ca40b4519bd31318e8d05ee592839414b78fad38d06d42cd16` |
| `rk3399pro_loader_v1.30.126.bin` | 444K | `274f2358813c719270895f67369e4a0aa59adba9f32e57be69c24bf89518af0a` |
| `rk3506_spl_loader_v1.06.111.bin` | 272K | `daffbdcee4f3803fab1ff0c4702e2d1922c8f7fd485f289529947fceee4f15e7` |
| `rk3528_spl_loader_v1.11.106.bin` | 468K | `3999b6d0919436880cd5821f8ebb20e332229b3c630c9cd0189502bd9e5d5f58` |
| `rk3562_spl_loader_v1.07.107.bin` | 468K | `01e13625974638c23919e7622ef2c29759a4be30d58cbfa9e746929cf853e55b` |
| `rk356x_spl_loader_v1.23.114.bin` | 472K | `cc36c4b1585ba4c70e6e00d3d916057c9585ea06ec0dae2ae161655dcbfc2590` |
| `rk3576_spl_loader_v1.09.108.bin` | 768K | `d124d976bfc6a3fc06ffffa6cdd895fd3c107652c22b0a9e2b820cfa45cee7fb` |
| `rk3582_spl_loader_v1.19.113.bin` | 484K | `41ab8c2120420c7b8581010d5f27f23010d931e3be8463e8c9574fc8a5aad65b` |
| `rk3583_spl_loader_v1.19.113.bin` | 484K | `41ab8c2120420c7b8581010d5f27f23010d931e3be8463e8c9574fc8a5aad65b` |
| `rk3588_spl_loader_v1.19.113.bin` | 484K | `5f183b8688e51910dbb5d9f558feca10930b24d4476bcb622212b3744371db9a` |
| `rknpu_lion_loader_v1.04.103.bin` | 160K | `cb1088b49cec597a474ff313bbfb6bd05180fee40bff5f97a6eb474ef5894c41` |
| `rv1103b_download_v1.05.100.bin` | 248K | `10bdb0a5b988aadccd0653b628ced41df6832693f896da927818f77200763f07` |
| `rv1106_download_v1.15.108.bin` | 276K | `4ec99f390919179ff2d080731ccea70a6c2cbe6c7c6b9f15f59f38d743b7b245` |
| `rv110x_loader_v1.12.126.bin` | 236K | `37831211c38e8e57a978b96bdfc3ad524f3cb11bda04b72d85622861752f0d80` |
| `rv1126_spl_loader_v1.14.110.bin` | 292K | `ddf4402870f8c7261ce4f51b92337deda1b785ed6f9138211cca77f5729229b0` |
| `rv1126b_spl_loader_v1.03.103.bin` | 436K | `fa4d6ed2c51e9c56523a46bf7447bbf49b4d8822b34954027be4c8c6f419d0e0` |
| `rv1126bp_spl_loader_v1.03.103.bin` | 436K | `007bdd8ea81ac77f4e3fcde880b407009cb9227690b89036c45fa2a44584fa1f` |
