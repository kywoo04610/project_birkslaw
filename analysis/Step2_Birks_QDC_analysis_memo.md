# SND@LHC Birks’ Law Project — Verification Step 2 분석 메모

작성일: 2026-07-20  
분석 단계: Birks 적용 MC, Birks 미적용 MC, 2023 H8 test-beam data의 MuFilter Upstream QDC 비교

## 1. 분석 목적

Step 2의 목적은 다음 세 표본의 MuFilter 반응을 비교하여, 새로 구현한 Birks 보정이 시뮬레이션 결과에 어떤 영향을 주는지 확인하는 것이다.

1. Birks’ Law를 적용하여 새로 생성한 MC
2. 기존의 Birks 미적용 MC
3. 2023년 H8 test-beam data

현재 비교하는 양은 scintillator에서 직접 생성된 광자 수나 step별 에너지 손실이 아니라, digitization 이후의 `Digi_MuFilterHits` QDC이다. 따라서 관측되는 차이는 Birks quenching뿐 아니라 광수집, SiPM 응답, channel calibration 및 digitization 모델의 영향도 포함한다.

## 2. 사용한 표본

| E, Particle |       Birks MC        |      No-Birks MC        |                 Data                   |
|-------------|----------------------:|------------------------:|---------------------------------------:|
| 100 GeV, π⁺ | 새로 생성한 100 events | 기존 표본 20,000 events | run 100630, 13 files, 약 1,203만 events |
| 300 GeV, π⁻ | 새로 생성한 100 events | 4개 파일, 총 16,000 events | run 100639, 58 files, 5,800만 events |

Birks MC는 수정한 `MuFilter.cxx`를 포함하는 sndsw를 빌드한 뒤 생성하고 digitization하였다. 두 Birks MC 파일 모두 `cbmsim` tree, 100 entries 및 `Digi_MuFilterHits` branch가 존재함을 확인하였다.

Birks 함수에는 다음 조건을 사용하였다.

\[
E_{\mathrm{vis}}=
\frac{E_{\mathrm{dep}}}
{1+k_1(dE/dx)_{\mathrm{mass}}+k_2(dE/dx)_{\mathrm{mass}}^2},
\]

\[
(dE/dx)_{\mathrm{mass}}
=\frac{E_{\mathrm{dep}}/\mathrm{MeV}}
{(\Delta x/\mathrm{cm})\rho}.
\]

- 잠정적인 ATLAS TileCal 값: `k1 = 0.02002`, `k2 = 0`
- charged particle에만 적용
- zero energy deposit, zero step size 및 비정상적인 density에 대한 guard 포함
- `|q| > 1`이면 `k1 × 7.2/12.6` 적용

이 상수들은 아직 SND scintillator에 맞춰 측정하거나 fitting한 값이 아니라는 점이 중요하다.

## 3. 분석 observable

### 3.1 Event별 total US QDC

각 event에 대해 Upstream MuFilter 전체에서 유효한 positive QDC를 더하였다.

- `system == 2`인 hit만 선택
- `GetAllSignals(mask=True, positive=True, use_small_sipms=False)` 사용
- small SiPM channel은 제외

이 값은 event 전체의 shower response와 Birks 보정에 따른 총 반응 변화를 보기 위한 observable이다.

### 3.2 US1–US3, bar 4와 5의 channel response

각 station의 bar 4와 5에서 SiPM channel별 mean positive QDC를 비교하였다.

- US1, US2, US3는 각각 plane 0, 1, 2
- plot의 error bar는 event 분포의 표준편차가 아니라 mean의 standard error이다.

## 4. Selection의 발전 과정

### 4.1 Preliminary analysis

처음에는 각 표본의 앞 100 events를 별도 selection 없이 분석하였다. 이때 data의 median total QDC가 100 GeV에서 약 1.8, 300 GeV에서 약 3.5로 나타났다. 이는 임의의 data event 대부분이 원하는 pion shower event가 아니라 low-activity/noise event임을 보여주었다.

따라서 이 preliminary 결과는 물리 비교에 사용하지 않고, data selection이 필요하다는 진단용 결과로만 남겼다.

### 4.2 Bar-coincidence selection

두 번째 분석에서는 각 event가 US1, US2, US3 모두에서 bar 4 또는 bar 5의 positive signal을 하나 이상 갖도록 요구하였다.

| 표본 | 선택 결과 |
|------------------|------------------:|
| Birks MC 100 GeV | 100개 중 98개 선택 |
| No-Birks MC 100 GeV | 111개 scan 후 100개 선택 |
| Data 100 GeV | 9,799개 scan 후 100개 선택 |
| Birks MC 300 GeV | 100개 중 100개 선택 |
| No-Birks MC 300 GeV | 100개 중 100개 선택 |
| Data 300 GeV | 2,040개 scan 후 100개 선택 |

이 selection으로 data QDC는 현실적인 범위로 올라왔지만, 여전히 다른 종류의 trigger가 섞일 가능성이 있었다.

### 4.3 Final data selection

최종 분석에서는 위의 bar-coincidence 조건에 더하여, real data에만 event header의 fast noise-filter 정보를 적용하였다.

요구한 조건은 다음 세 flag가 모두 `True`인 것이다.

- `SciFi`
- `SciFi_Total`
- `US_Total`

이 조합은 조사한 파일에서 주로 `flags = 738197504 = 0x2c000000`에 해당하였다. 100,000 events를 조사했을 때 이 flag를 가진 bar-selected event의 total US QDC는 다음과 같았다.

| Data | Events | Mean QDC | Median QDC |
|----------------------------|------:|---------:|---------:|
| 100 GeV, flag `0x2c000000` | 6,008 | 4,656.22 | 4,612.37 |
| 300 GeV, flag `0x2c000000` | 5,041 | 11,639.07 | 11,753.40 |

반면 `US_Total`만 참인 `0x20000000` 표본은 median이 각각 약 184와 87로 낮아, low-activity/noise event가 많이 포함된 것으로 판단하였다.

`GetBeamMode()`는 조사한 event에서 모두 0이었고, `isNoBeam()`도 모두 `False`였으므로 test-beam pion selection에 유용하지 않았다. MuFilter hit의 `isValid()` 검사에서는 invalid hit가 발견되지 않았다.

주의할 점은 `0x2c000000`이 코드상 명시적으로 정의된 “pion trigger” 이름은 아니라는 것이다. 현재 selection은 detector coincidence를 이용한 실용적인 event selection이다.

## 5. 최종 Step 2 결과표

| 에너지 | 표본 | 선택 events | Mean total US QDC | Median total US QDC | Standard deviation |
|---------|----------|---:|----------:|---------:|---------:|
| 100 GeV | Birks MC | 98 | 10,717.55 | 9,990.87 | 6,727.19 |
| 100 GeV | No-Birks MC | 100 | 13,139.69 | 11,462.55 | 7,072.66 |
| 100 GeV | Data | 100 | 4,117.94 | 4,534.97 | 3,062.84 |
| 300 GeV | Birks MC | 100 | 34,201.32 | 33,646.11 | 17,534.73 |
| 300 GeV | No-Birks MC | 100 | 37,791.17 | 34,879.06 | 17,555.79 |
| 300 GeV | Data | 100 | 11,632.53 | 11,794.44 | 4,224.16 |

## 6. 정량적 비교

### 6.1 Birks 적용에 따른 MC mean 감소

No-Birks MC를 기준으로 total US QDC mean의 감소율을 계산하면 다음과 같다.

| 에너지 | Birks 적용 전 | Birks 적용 후 | Mean 감소율 |
|---------|----------:|----------:|----------:|
| 100 GeV | 13,139.69 | 10,717.55 | **18.4%** |
| 300 GeV | 37,791.17 | 34,201.32 | **9.5%** |

따라서 구현한 Birks 보정은 예상한 방향대로 전체 MC response를 낮추고 있다. 효과의 크기는 이 표본에서 100 GeV가 300 GeV보다 크게 나타났다.

### 6.2 MC와 data의 절대 scale

Mean 기준 MC/data 비율은 다음과 같다.

| 에너지 | Birks MC / Data | No-Birks MC / Data |
|---------|-----:|-----:|
| 100 GeV | 2.60 | 3.19 |
| 300 GeV | 2.94 | 3.25 |

Birks 적용으로 MC가 data에 가까워지기는 하지만, 절대 QDC scale에는 여전히 약 2.6–2.9배의 차이가 남는다. 따라서 현재 차이를 Birks quenching 하나만으로 설명할 수 없다.

### 6.3 300 GeV / 100 GeV response 비율

Mean total QDC의 에너지 간 비율은 다음과 같다.

| 표본 | 300 GeV / 100 GeV |
|------|------------------:|
| Data | 2.82 |
| No-Birks MC | 2.88 |
| Birks MC | 3.19 |

절대 scale에서는 Birks MC가 data 쪽으로 이동하지만, 두 에너지 사이의 상대적인 scaling은 현재 표본에서 No-Birks MC가 data에 더 가깝다. 다만 100 GeV와 300 GeV가 서로 다른 charge의 pion이고, Birks MC 통계도 작기 때문에 이 비율만으로 모델의 우열을 판단해서는 안 된다.

## 7. Plot에서 관찰되는 특징

### 7.1 Total US QDC distribution

- Birks MC 분포는 전반적으로 No-Birks MC보다 낮은 QDC 방향으로 이동한다.
- 이동 방향은 data와의 차이를 줄이는 방향이다.
- 그러나 data 분포는 MC보다 훨씬 낮고 상대적으로 좁아, 세 분포가 완전히 일치하지 않는다.
- 100 GeV data에는 final selection 이후에도 매우 낮은 QDC event가 일부 남아 있다.
- histogram이 `density=True`로 작성되었다면 y축은 “Normalized events”보다는 “Probability density”가 더 정확하다.

### 7.2 Channel response

- Data는 channel에 따라 mean QDC가 달라지는 구조를 보인다.
- MC channel response는 거의 평평하여 실제 detector의 channel별 gain, attenuation 또는 calibration 차이가 충분히 재현되지 않는 것으로 보인다.
- 일부 station/bar에서는 Birks와 No-Birks의 국소적인 순서가 뒤집혀 보인다. 두 MC가 동일 event를 짝지어 비교한 표본이 아니고 각각 100개 정도의 독립적인 shower 표본이므로, 이를 Birks 보정이 빛을 증가시켰다는 뜻으로 해석해서는 안 된다.
- global total response에서는 Birks MC가 일관되게 감소한다.

## 8. 현재 단계에서 가능한 결론

1. Birks 함수는 실행 가능한 형태로 sndsw에 구현되었고, simulation 및 digitization이 정상적으로 완료되었다.
2. 구현한 보정은 MC의 total US QDC를 예상한 방향으로 감소시킨다.
3. 감소량은 현재 표본의 mean 기준 약 18.4% at 100 GeV, 약 9.5% at 300 GeV이다.
4. Birks 적용 후 MC의 절대 response는 No-Birks MC보다 data에 가까워진다.
5. 그러나 상당한 MC–data 차이가 남아 있어, 현재 결과만으로 “Birks’ Law가 SND data를 잘 설명한다”고 결론 내릴 수 없다.
6. 반대로 현재의 불일치만으로 Birks’ Law가 틀렸다고 결론 내릴 수도 없다. 비교에는 Birks 외의 detector response와 sample 구성 차이가 포함되어 있기 때문이다.

## 9. 주요 한계점

### 9.1 작은 Birks MC 통계

Birks MC는 에너지당 100 events뿐이며, 100 GeV에서는 selection 후 98 events이다. Hadronic shower fluctuation이 커서 mean과 channel별 결과의 통계적 변동이 크다.

### 9.2 Birks와 No-Birks MC가 paired sample이 아님

두 표본은 동일한 primary event와 random seed를 공유하는 event-by-event 비교가 아니다. 따라서 observed difference에는 Birks 효과뿐 아니라 독립적인 shower fluctuation 및 생성 설정 차이가 포함될 수 있다.

### 9.3 사용한 event 수의 비대칭

기존 No-Birks MC와 data에는 훨씬 많은 event가 있지만, 현재 최종 비교에서는 각 표본에서 100 selected events만 사용하였다. 큰 표본이 제공하는 통계적 장점을 아직 활용하지 못했다.

### 9.4 Data selection의 불완전성

최종 selection은 bar coincidence와 fast-filter 조합을 이용한 경험적인 선택이다. 전용 pion trigger 정의나 beam-track matching을 직접 적용한 것은 아니다. 일부 low-QDC outlier도 남아 있다.

### 9.5 절대 QDC calibration 및 digitization 영향

비교 대상이 QDC이므로 scintillation quenching 외에도 다음 효과가 포함된다.

- light collection 및 attenuation
- SiPM gain과 saturation
- channel별 calibration
- masking 및 threshold
- electronics/digitization model

MC가 data보다 2.6배 이상 큰 원인이 Birks 상수 하나라고 가정할 수 없다.

### 9.6 MC의 이상적으로 평평한 channel response

MC와 data의 channel별 패턴이 다르므로, detector non-uniformity가 충분히 모델링되었는지 별도 검증이 필요하다.

### 9.7 두 beam 조건의 차이

100 GeV는 π⁺, 300 GeV는 π⁻이므로 두 결과의 차이를 순수한 energy dependence로만 해석할 수 없다.

### 9.8 Birks parameter의 잠정성

현재 `k1`, `k2`와 high-charge correction은 ATLAS에서 가져온 잠정값이다. SND MuFilter의 scintillator 재료와 readout에 맞는 최적값이라고 확인된 것은 아니다.

### 9.9 직접적인 Birks curve 검증이 아님

이번 분석은 여러 step과 shower가 합쳐진 digitized QDC를 비교한다. 논문에서처럼 측정된 light output을 stopping power의 함수로 직접 fitting한 분석은 아니다. 따라서 이는 Birks 구현의 detector-level 영향 확인이지, Birks 식 자체의 정밀 검증은 아니다.

## 10. 다음 단계 권고

1. Birks MC 통계를 충분히 늘린다.
2. 가장 중요한 control로, 동일한 random seed와 동일한 simulation/digitization 설정을 사용하여 Birks ON/OFF paired samples를 만든다.
3. 전체 No-Birks MC와 더 많은 selected data event를 사용하고, bootstrap 또는 표준오차로 mean·median·ratio의 불확도를 계산한다.
4. 긴 tail의 영향을 줄이기 위해 mean뿐 아니라 median, truncated mean 또는 적절한 분포의 MPV도 비교한다.
5. supervisor에게 `SciFi && SciFi_Total && US_Total` selection이 test-beam pion 비교에 적절한지 확인한다.
6. 가능하면 beam position/track 조건을 추가하여 bar 4–5를 실제로 통과한 event를 선택한다.
7. data와 MC의 QDC calibration, channel gain 및 attenuation 처리의 일관성을 확인한다.
8. 위 control이 확보된 뒤에만 `k1`, `k2` parameter scan 또는 fitting을 고려한다.

## 11. 재현 관련 파일 구분

- `analyze_qdc_preliminary.py`: selection 없이 앞부분 event를 확인한 진단용 분석
- `analyze_qdc_selected.py`: US1–US3의 bar 4/5 coincidence를 적용한 중간 분석
- `analyze_qdc_final.py`: bar coincidence와 real-data fast-filter 조건을 적용한 최종 분석
- `results/`: preliminary 결과
- `results_selected/`: bar-selected 결과
- `results_final/`: 현재 Step 2 최종 결과

## 12. 한 문장 요약

현재 구현한 Birks 보정은 SND MC의 총 QDC를 예상대로 낮추고 data 방향으로 이동시키지만, 통계·selection·calibration·unpaired sample의 한계가 크므로 지금 단계의 결과는 **구현 효과의 확인**으로 볼 수 있으며 **Birks’ Law의 data 적합성에 대한 최종 검증**으로 보기는 어렵다.
