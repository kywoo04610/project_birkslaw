// ATLAS의 TileGeoG4SDCalc.cc에서 Birks Law 관련 부분만 가져온 코드입니다.
// 실행용이 아닌, 기록용 코드입니다. 실제로는 ATLAS의 TileGeoG4SDCalc.cc와 TileGeoG4SDCalc.hh를 참고하시기 바랍니다.


// BirkLaw() 함수 전체 구현 (856~909행, 함수가 길어서 분할하여 작성함)
// 함수 및 수식 설명
// 여기서 설명하는 일반적인 식은
// edep = destep / (1. + RKB*dedx + C*(dedx)**2)
// 이며, destep은 현재 step에서 입자가 물질에 전달한 에너지
// (즉, G4Step::GetTotalEnergyDeposit() * G4Track::GetWeight())이고, 
// dedx는 현재 step에서 입자가 물질에 전달한 에너지를 step 길이와 물질 밀도로 나눈 값이다. 
// RKB와 C는 Birks Law의 상수이며, m_birk1과 m_birk2로 정의되어 있다. 
// 이 함수는 Birks Law를 적용하여 보정된 에너지를 반환한다. 
// 이 함수는 G4Step 객체를 입력으로 받아, 현재 step에서 입자가 물질에 전달한 에너지를 계산하고, 
// Birks Law를 적용하여 보정된 에너지를 반환한다. 
// -----------------------------------------------------------
G4double TileGeoG4SDCalc::BirkLaw(const G4Step* aStep) const
{
  // *** apply BIRK's saturation law to energy deposition ***
  // *** only organic scintillators implemented in this version MODEL=1
  //
  // Note : the material is assumed ideal, which means that impurities
  //        and aging effects are not taken into account
  //
  // algorithm : edep = destep / (1. + RKB*dedx + C*(dedx)**2)
  //
  // the basic units of the coefficient are g/(MeV*cm**2)
  // and de/dx is obtained in MeV/(g/cm**2)
  //
  // exp. values from NIM 80 (1970) 239-244 :
  //
  // RKB = 0.013  g/(MeV*cm**2)  and  C = 9.6e-6  g**2/((MeV**2)(cm**4))
// -----------------------------------------------------------


// step 정보 가져오기
// scintillator의 물질 이름
// step에서 침적된 에너지
// Monte Carlo weitght
// 현재 물질
// 입자 전하를 가져온다.
// -----------------------------------------------------------
  const G4String myMaterial = "tile::Scintillator";
  const G4double destep = aStep->GetTotalEnergyDeposit() * aStep->GetTrack()->GetWeight();
  //  doesn't work with shower parameterisation
  //  G4Material* material = aStep->GetTrack()->GetMaterial();
  //  G4double charge      = aStep->GetTrack()->GetDefinition()->GetPDGCharge();
  const G4Material* material = aStep->GetPreStepPoint()->GetMaterial();
  const G4double charge = aStep->GetPreStepPoint()->GetCharge();
// -----------------------------------------------------------


// 적용 조건
// 입자 전하가 0이 아니고, 
// 현재 물질이 scintillator인 경우에만 Birks Law를 적용한다.
// -----------------------------------------------------------
  // --- no saturation law for neutral particles ---
  // ---  and materials other than scintillator  ---
  if ( (charge != 0.) && (material->GetName() == myMaterial)) {
// -----------------------------------------------------------


// 결과 변수와 zero-step 확인
// step length가 0이 아닌 경우에만 dE/dx를 계산한다.
// -----------------------------------------------------------
    G4double response = 0.;
    if (aStep->GetStepLength() != 0) {
// -----------------------------------------------------------


// 유효 Birks 상수 결정
// 기본적으로 rkb = m_birk1로 설정되어 있으며,
// 입자 전하가 1보다 큰 경우에는 rkb를 7.2/12.6로 보정한다. 
// 이는 알파 입자 데이터를 기반으로 한 보정이며, MODEL=1인 경우에만 적용된다. 
// 현재 step에서 입자가 물질에 전달한 에너지를 step 길이와 물질 밀도로 나눈 값을 dedx로 계산한다. 
// 최종적으로 Birks Law를 적용하여 보정된 에너지를 response에 저장한다. 
// -----------------------------------------------------------
      G4double rkb = m_birk1;
      // --- correction for particles with more than 1 charge unit ---
      // --- based on alpha particle data (only apply for MODEL=1) ---
      if (fabs(charge) > 1.0) {
        rkb *= 7.2 / 12.6;
      }
// -----------------------------------------------------------


// mass stopping power 계산
// 수식으로는 dE/dx = deltaE / (deltax * density)로 계산된다.
// 단위는 MeV/(g/cm^2) = MeV*cm^2/g이다.
// -----------------------------------------------------------
      const G4double dedx = destep / (aStep->GetStepLength()) / (material->GetDensity());
// -----------------------------------------------------------


// Birks correction 적용
// 현재 기본값에서는 m_birk2가 0이므로, 실제로는 rkb만 적용된다.
// -----------------------------------------------------------
      response = destep / (1. + rkb * dedx + m_birk2 * dedx * dedx);
// -----------------------------------------------------------


// zero-step 처리
// step length가 0이면 Birks correction을 적용하지 않고,
// 원래 energy deposit를 그대로 반환한다.
// -----------------------------------------------------------
    }
    else {
      ATH_MSG_DEBUG("BirkLaw() - Current Step in scintillator has zero length." << "Ignore Birk Law for this Step");
      response = destep;
    }
// -----------------------------------------------------------


// 디버깅용 출력
// 현재 주석 처리되어 있으므로 실행되지는 않는다.
// Birks correction 적용 전과 후의 에너지를 keV 단위로 출력한다.
// -----------------------------------------------------------
    // if (-2==verboseLevel) {
    // G4cout << " Destep: " << destep/CLHEP::keV << " keV"
    // << " response after Birk: "  << response/CLHEP::keV << " keV" << G4endl;
    // }
// -----------------------------------------------------------


// 결과 반환
// Birks Law 적용 조건을 만족하면 response를 반환하고, 
// 그렇지 않으면 원래 energy deposit인 destep를 반환한다.
// -----------------------------------------------------------
    return response;
  }
  else {
    return destep;
  }
// -----------------------------------------------------------
}


// 옵션 초기화 (70행)
// .hh 파일에 정의된 m_doBirk값을 실제 simulation option으로 복사한다.
// -----------------------------------------------------------
m_options.doBirk = m_doBirk.value();
// -----------------------------------------------------------


// 설정 확인 (168~171행)
// 시뮬레이션 시작 시 다음을 로그에 출력한다.
// Birks correction 활성화 여부,
// 실제 사용하는 Birks 상수 값(m_birk1, m_birk2)을 출력한다.
// 상수를 외부 설정에서 덮어쓸 수 있으므로,
// 실행 시 실제 값을 확인하려면 이 로그가 중요하다.
// -----------------------------------------------------------
ATH_MSG_DEBUG(
    "Using doBirk = " 
    << (m_options.doBirk ? "true" : "false")
);
if(m_options.doBirk) {
    ATH_MSG_INFO(
        "Using Birksk1="<<m_birk1.value()
        <<", Birksk2="<<m_birk2.value()
    );
}
// -----------------------------------------------------------


// 실제 호출 (432-433행)
// -----------------------------------------------------------
// Take into account Birk's saturation law in organic scintillators.
const G4double edep = 
    (m_options.doBirk) 
    ? this->BirkLaw(aStep) 
    : aStep->GetTotalEnergyDeposit() 
        * aStep->GetTrack()->GetWeight();
// -----------------------------------------------------------