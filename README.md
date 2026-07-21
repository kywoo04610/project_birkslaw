# SND@LHC Birks' Law — MuFilter QDC Study

이 저장소는 SND@LHC MuFilter scintillator simulation에 Birks' law quenching을 적용하고, digitization 이후의 Upstream MuFilter QDC를 기존 MC 및 2023 CERN H8 test-beam data와 비교하는 프로젝트의 코드와 작업 기록을 보관한다.

이 문서는 새 ChatGPT 대화나 새로운 작업 환경에서도 프로젝트를 즉시 이어갈 수 있도록 작성한 인수인계 문서다. 아래에서 **검증 완료된 과거 결과**, **현재 코드의 실제 상태**, **최근 15k 분석에서 발견한 문제**, **다음에 해야 할 작업**을 구분한다.

## 1. 연구 목표

비교 대상은 다음 세 표본이다.

1. Birks' law를 적용하여 새로 생성한 MC (`Birks MC`)
2. 기존 Birks 미적용 MC (`No-Birks MC`)
3. 2023 H8 test-beam real data (`Data`)

주요 질문은 다음과 같다.

- 새 Birks 구현이 정상적으로 simulation/digitization을 통과하는가?
- Birks quenching이 MC의 total US QDC를 예상대로 감소시키는가?
- 감소한 MC response가 data에 더 가까워지는가?
- 남은 MC–data 차이를 Birks parameter만으로 설명할 수 있는가?

현재 observable은 Geant4 step의 직접적인 light yield가 아니라 digitization 이후 `Digi_MuFilterHits`의 QDC다. 따라서 결과에는 Birks quenching 외에도 light collection, attenuation, SiPM response, gain, saturation, masking, threshold, calibration 및 digitization model이 포함된다.

## 2. 물리 모델과 구현

사용한 형태는 다음과 같다.

$$
E_{\mathrm{vis}} = \frac{E_{\mathrm{dep}}}{1 + k_1(dE/dx)_{\mathrm{mass}} + k_2(dE/dx)_{\mathrm{mass}}^2},
$$

$$
(dE/dx)_{\mathrm{mass}} = \frac{E_{\mathrm{dep}}/\mathrm{MeV}}{(\Delta x/\mathrm{cm})\rho}.
$$

현재 적용 조건:

- 잠정 상수: `k1 = 0.02002`, `k2 = 0`
- charged particle에만 적용
- zero energy deposit, zero step length, 비정상 density에 대한 guard 포함
- `|q| > 1`이면 `k1 * 7.2 / 12.6` 적용

이 상수는 ATLAS TileCal 계열 값을 참고한 잠정값이며, SND MuFilter scintillator에 맞춰 측정하거나 fitting한 최종값이 아니다.

## 3. 데이터셋

### 3.1 Beam conditions

| Energy | Particle | Data run | Data tree |
|---|---|---:|---|
| 100 GeV | $\pi^+$ | `100630` | `rawConv` |
| 300 GeV | $\pi^-$ | `100639` | `rawConv` |

### 3.2 Current paths in `analyze_qdc_final.py`

현재 작업공간의 코드는 다음 경로를 사용한다.

- Birks MC: `/eos/user/y/ykim/project_birkslaw/birks_samples_10k/...`
- No-Birks 100 GeV: `/eos/experiment/sndlhc/MonteCarlo/testbeam2023/2mmRangeCut/100GeV_211/...`
- No-Birks 300 GeV: `/eos/experiment/sndlhc/MonteCarlo/testbeam2023/2mmRangeCut/300GeV_-211/...`
- Data 100 GeV: `/eos/experiment/sndlhc/convertedData/commissioning/testbeam_June2023_H8/run_100630/...`
- Data 300 GeV: `/eos/experiment/sndlhc/convertedData/commissioning/testbeam_June2023_H8/run_100639/...`

> **중요:** 최근에는 에너지별 15,000-event Birks MC를 생성했다. 그러나 현재 저장된 `analyze_qdc_final.py`는 아직 `birks_samples_10k`를 가리킨다. 최종 15k 분석 전 반드시 실제 EOS 디렉터리 이름을 확인하고 `DATASETS`의 두 Birks 경로를 수정해야 한다.

15k 생성 관련 파일은 `birks_15k/`에 있다.

## 4. Analysis observable

### 4.1 Event-by-event total US QDC

각 selected event에서 Upstream MuFilter 전체의 positive large-SiPM QDC를 합산한다.

- `system == 2`인 MuFilter hit만 사용
- `GetAllSignals(mask=True, positive=True, use_small_sipms=False)` 사용
- small SiPM channel 제외
- 모든 US bar의 positive QDC를 event total에 포함

### 4.2 Channel response

US1–US3의 bar 4와 5에서 channel별 mean positive QDC를 비교한다.

- US1, US2, US3 = plane 0, 1, 2
- channels: `0, 1, 3, 4, 6, 7, 8, 9, 11, 12, 14, 15`
- error bar는 event 분포의 표준편차가 아니라 mean의 standard error

## 5. 현재 analysis selection

현재 `analyze_qdc_final.py`는 Data와 두 MC 모두에 동일하게 다음 조건을 적용한다.

1. `len(Digi_ScifiHits) > min_scifi_hits` (기본값 200)
2. US1, US2, US3 각각에서 bar 4 또는 5에 positive large-SiPM signal이 하나 이상 존재

즉 required plane set `{0, 1, 2}`가 모두 충족되어야 한다.

### Selection 역사와 주의사항

초기 분석에서는 Data event 대부분이 low-activity/noise였기 때문에 bar coincidence와 event-header fast-filter flag를 조사했다. 과거 100-event 검증에서는 `SciFi && SciFi_Total && US_Total` 조합(주로 `0x2c000000`)도 활용했다.

하지만 **현재 작업공간의 코드에는 event-header fast-filter flag selection이 없다.** 현재 코드는 SciFi hit multiplicity와 US bar 4/5 coincidence만 사용한다. 새 대화에서 과거 메모의 “final data selection”과 현재 코드를 동일하다고 가정하면 안 된다.

`GetBeamMode()`와 `isNoBeam()`은 조사 당시 유용한 pion selection을 제공하지 않았고, MuFilter `isValid()` 검사에서도 invalid hit는 발견되지 않았다.

## 6. 명령행 옵션의 정확한 의미

```text
--max-events
```

- dataset별 **selection 통과 event 수**의 상한
- `-1`: 전체 sample 유지
- `15000`: selection을 통과한 첫 15,000개가 쌓이면 즉시 중단
- scanned raw entry 수 제한이 아님

```text
--max-scanned-events
```

- dataset별 스캔할 input entry 수의 상한
- `-1`: 전부 스캔

```text
--file-check-events
```

- Data 파일마다 별도 cutflow 검사를 위해 읽는 entry 수
- 본 분석과 별도의 추가 순회이므로 큰 값이나 `-1`은 실행시간을 크게 늘림
- histogram만 필요할 때 `1`로 두면 사실상 중복 전체 순회를 피할 수 있음

```text
--min-scifi-hits
```

- `Digi_ScifiHits`가 이 값보다 커야 함
- 현재 사용값: `200`

## 7. 현재 코드가 생성하는 출력

- `total_us_qdc_100GeV.png`
- `total_us_qdc_300GeV.png`
- `channel_response_100GeV.png`
- `channel_response_300GeV.png`
- `total_us_qdc_summary.csv`
- `data_file_by_file_cutflow.csv`

현재 histogram은 세 sample을 합친 값의 99.5 percentile을 upper edge로 사용하고 40 bins로 그린다. `density=True`이므로 y축의 정확한 의미는 probability density다.

> **현재 코드에는 `.npz` QDC cache 저장과 histogram underflow/overflow 출력이 없다.** 대화 중 캐시 기능을 추가한 별도 완성본 `analyze_qdc_final(4).py`를 만들었지만, 사용자는 최근 15k 제한 실행을 기존 코드로 수행했다. 어느 파일을 CERN에 배치했는지 반드시 확인해야 한다.

## 8. 검증 완료된 과거 Step 2 결과 (100 selected events)

아래 값은 작은 Birks MC(에너지당 약 100 events)를 사용한 과거 검증 결과다. 최근 10k/15k 생산 결과와 혼동하지 않는다.

| Energy | Sample | Selected | Mean total US QDC | Median | Std. dev. |
|---|---|---:|---:|---:|---:|
| 100 GeV | Birks MC | 98 | 10,717.55 | 9,990.87 | 6,727.19 |
| 100 GeV | No-Birks MC | 100 | 13,139.69 | 11,462.55 | 7,072.66 |
| 100 GeV | Data | 100 | 4,117.94 | 4,534.97 | 3,062.84 |
| 300 GeV | Birks MC | 100 | 34,201.32 | 33,646.11 | 17,534.73 |
| 300 GeV | No-Birks MC | 100 | 37,791.17 | 34,879.06 | 17,555.79 |
| 300 GeV | Data | 100 | 11,632.53 | 11,794.44 | 4,224.16 |

과거 표본에서 Birks 적용 후 mean 감소율:

- 100 GeV: 약 18.4%
- 300 GeV: 약 9.5%

Birks MC / Data mean ratio:

- 100 GeV: 약 2.60 (No-Birks: 3.19)
- 300 GeV: 약 2.94 (No-Birks: 3.25)

따라서 Birks 보정은 MC response를 예상 방향으로 낮추고 data 쪽으로 이동시켰지만, 절대 scale 차이는 크게 남았다. 이 결과는 구현 효과의 확인이지 Birks law의 data 적합성에 대한 최종 검증이 아니다.

## 9. 최근 대규모 분석 경과와 발견한 표본추출 문제

### 9.1 실행시간 병목

Data는 매우 크다(100 GeV 약 1,200만 events, 300 GeV 약 5,800만 events로 파악). 전체 file-by-file 검사 후 본 분석에서 같은 Data를 다시 읽으면 사실상 Data를 두 번 순회한다.

가장 간단한 실행시간 개선은 `--file-check-events 1`이다. 이것은 본 QDC 분석 결과를 바꾸지 않고 별도 file-check 순회만 최소화한다. 단, 생성되는 file-by-file cutflow는 물리적으로 유용하지 않다.

### 9.2 `--max-events 15000` 실험

실행시간을 줄이기 위해 다음 형태로 기존 코드를 실행했다.

```bash
python3 analyze_qdc_final.py \
  --max-events 15000 \
  --max-scanned-events -1 \
  --file-check-events 1 \
  --min-scifi-hits 200 \
  --output-dir results_selected_15k \
  2>&1 | tee results_selected_15k.log
```

100 GeV와 300 GeV plot은 생성되었으나, 특히 300 GeV Data 분포가 과거 결과와 지나치게 달랐다.

원인은 단순히 “15,000 events라서 통계가 부족함”이 아니다. histogram은 `density=True`이고 15,000 events는 shape 비교에 충분하다. 핵심은 현재 구현이 **전체 selected Data 중 random 15,000개**를 뽑는 것이 아니라 **파일 목록 앞부분에서 처음 selection을 통과한 15,000개**를 모은 뒤 즉시 종료한다는 점이다. 이 표본은 특정 file/run segment, beam condition 또는 calibration 상태에 편향될 수 있다.

따라서 최근 `results_selected_15k`의 Data plot을 최종 물리 결과로 사용하면 안 된다.

## 10. Random sampling에 대한 올바른 이해

전체 selection 통과 event 중 균일하게 random 15,000개를 얻으려면 selection 판정을 위해 전체 Data를 한 번은 스캔해야 한다. 메모리는 reservoir sampling으로 제한할 수 있지만 전체 ROOT I/O 시간은 피할 수 없다.

Reservoir sampling 개념:

```python
rng = np.random.default_rng(42)
passed_count = 0
reservoir = []

# selection을 통과한 각 event에 대해
passed_count += 1
if len(reservoir) < 15000:
    reservoir.append(event_payload)
else:
    j = rng.integers(0, passed_count)
    if j < 15000:
        reservoir[j] = event_payload
```

이 방식은 모든 passing event가 최종 reservoir에 포함될 확률을 동일하게 한다. 재현성을 위해 seed(예: 42)를 고정하고 README 및 output metadata에 기록해야 한다.

주의: total QDC뿐 아니라 channel-response plot도 동일한 random event subset을 사용하려면 event payload에 total QDC와 해당 event의 channel QDC를 함께 보관하거나, sampled entry identifiers를 저장한 뒤 처리해야 한다.

## 11. 권장 성능 개선 순서

1. Data 중복 순회 제거: histogram 분석 시 `--file-check-events 1`
2. 한 번의 전체 스캔에서 event-level QDC를 `.npz`로 저장
3. 이후 histogram range, binning, normalization은 ROOT를 다시 읽지 않고 cache에서 수행
4. 필요한 ROOT branches만 활성화 (`Digi_ScifiHits`, `Digi_MuFilterHits`, 필요 시 header)
5. Python hit loop가 병목인지 profile한 뒤 무거운 event loop만 C++/RDataFrame으로 이동
6. 파일 단위 multiprocessing은 EOS I/O 포화 여부를 확인한 후 적용

`.py` 전체를 기계적으로 `.cpp`로 번역하는 것보다 PyROOT event/hit loop를 C++ 또는 RDataFrame으로 옮기는 편이 효과적이다. 다만 I/O가 병목이면 C++ 전환만으로 개선폭이 제한된다.

## 12. 다음 작업 — 우선순위 순서

새 대화에서 가장 먼저 아래를 수행한다.

1. CERN에서 실제 사용 중인 `analyze_qdc_final.py`가 구버전인지 캐시 버전인지 확인한다.
2. Birks MC 경로를 `birks_samples_10k`에서 실제 15k output 경로로 수정한다.
3. `.npz` cache 및 histogram range/bin width/underflow/overflow 진단을 통합한다.
4. random sampling 정책을 결정한다.
   - 최종 대표 표본: 전체 passing Data를 스캔하는 reservoir sampling
   - 빠른 진단: 여러 파일에서 균등 quota를 뽑는 stratified/file-balanced sampling (완전 균일 random은 아님)
5. 선택된 entry의 provenance를 저장한다: filename/file index, tree entry, run/event identifier(가능하면), random seed.
6. 소량 event로 문법·branch·selection·cache를 검증한다.
7. 최종 전체 스캔은 한 번만 실행하고 raw selected QDC cache를 보존한다.
8. cache 전용 plotting script를 별도로 만들어 range/binning/normalization을 빠르게 반복한다.

권장 최종 output 구성:

```text
results_random15k/
├── total_us_qdc_values_100GeV.npz
├── total_us_qdc_values_300GeV.npz
├── total_us_qdc_100GeV.png
├── total_us_qdc_300GeV.png
├── channel_response_100GeV.png
├── channel_response_300GeV.png
├── total_us_qdc_summary.csv
├── sampling_manifest.csv
├── run_config.json
└── analysis.log
```

## 13. Recommended execution modes

### Quick code check (not a final physics result)

```bash
python3 -m py_compile analyze_qdc_final.py

python3 analyze_qdc_final.py \
  --max-events 100 \
  --max-scanned-events 100000 \
  --file-check-events 1 \
  --min-scifi-hits 200 \
  --output-dir results_quick_test
```

### Full scan for cache/reservoir generation

정확한 명령은 reservoir sampling 옵션을 구현한 뒤 확정해야 한다. 기존 `--max-events 15000`만 사용하면 앞부분 편향이 재발하므로 최종 분석에 사용하지 않는다.

## 14. Interpretation rules

- `density=True`에서는 sample event 수가 같을 필요가 없다.
- 처음 15,000개와 전체에서 random 15,000개는 통계적으로 다른 표본설계다.
- Birks MC가 No-Birks MC보다 낮아지는 global trend는 구현 방향과 일치한다.
- 독립 MC sample의 channel별 국소적인 순서 역전은 shower fluctuation일 수 있다.
- Birks ON/OFF가 동일 primary event와 seed를 공유하지 않으므로 현재 비교는 paired comparison이 아니다.
- 100 GeV는 $\pi^+$, 300 GeV는 $\pi^-$이므로 차이를 순수 energy dependence로 해석하면 안 된다.
- MC–data 절대 scale 불일치는 Birks 상수 하나로 단정하지 않는다.
- parameter fitting은 selection, calibration, detector non-uniformity, paired sample 문제를 먼저 통제한 뒤 수행한다.

## 15. Known code issues

현재 `analyze_qdc_final.py`에서 확인된 사항:

- `channel_qdc = defaultdict(list)`가 연속 두 번 선언되어 있다. 결과에는 영향이 없지만 한 줄을 제거할 수 있다.
- Birks path가 10k directory를 가리킨다.
- `.npz` cache가 없다.
- histogram overflow 진단이 없다.
- y-axis label `Normalized events`는 `Probability density`가 더 정확하다.
- `max_events`는 앞에서부터 passing event를 모으므로 random sampling 옵션으로 사용하면 안 된다.
- file-by-file Data check에는 SciFi multiplicity cut이 포함되지 않아 본 analysis selection efficiency와 직접 동일하지 않다.

## 16. Repository/file guide

- `analyze_qdc_final.py`: 현재 QDC analysis main script
- `Step2_Birks_QDC_analysis_memo.md`: 2026-07-20 기준 상세 물리 분석 메모
- `birks_15k/`: 15k Birks MC generation/submission 관련 파일
- `birks_15k_generation_files.tar.gz`: 15k generation files archive
- `analyze_qdc_final(4).py` (대화에서 생성된 파일): cache/overflow 기능을 추가한 후보 버전. CERN 배치본과 diff 및 검증 필요

대용량 ROOT files와 재생성 가능한 결과 파일은 Git에 직접 올리지 말고 EOS 경로 및 manifest/checksum을 기록하는 방식을 권장한다.

## 17. Reproducibility checklist

최종 결과를 공유하기 전 아래를 기록한다.

- sndsw release/container 이름과 Git commit
- 수정한 `MuFilter.cxx` commit/diff
- Birks constants 및 unit convention
- MC input/output EOS paths와 file counts
- Data run과 file list
- selection 정의
- random seed 및 sampling method
- available/scanned/passing/retained event counts
- histogram bins/range 및 overflow count
- analysis code Git commit
- 실행 명령과 log

## 18. Current bottom line

Birks 구현은 MC total US QDC를 예상대로 감소시키며 과거 작은 표본에서는 data 방향으로 이동했다. 그러나 상당한 절대 scale 차이가 남고, 현재 대규모 비교는 Data sampling 편향 문제를 발견한 단계다. **다음 핵심 작업은 15k Birks 경로·cache 기능을 정리한 뒤, 전체 passing Data에서 재현 가능한 random 15,000개를 reservoir sampling하여 최종 비교를 다시 만드는 것**이다.

