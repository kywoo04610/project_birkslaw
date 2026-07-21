// ATLAS의 TileGeoG4SDCalc.hh에서 Birks Law 관련 부분만 가져온 코드입니다.
// 실행용이 아닌, 기록용 코드입니다. 실제로는 ATLAS의 TileGeoG4SDCalc.cc와 TileGeoG4SDCalc.hh를 참고하시기 바랍니다.


// BirkLaw 함수 선언
// BirkLaw라는 함수가 존재하며, 하나의 Geant4 step을 받아 보정된 에너지를 반환한다는 선언이다.
// G4Step은 Geant4에서 입자 시뮬레이션 중에 발생하는 한 단계(step)를 나타내는 객체이다. 
// 이 함수는 Birks Law를 적용하여 에너지 손실을 계산한다.
// -----------------------------------------------------------
/** @brief function to calculate Birks correction */
G4double BirkLaw(const G4Step* aStep) const;
// -----------------------------------------------------------

// 활성화 옵션
// true로 설정하면 Birks Law를 적용하여 에너지 손실을 계산하고, 
// false로 설정하면 적용하지 않는다.
// 기본값은 true로 설정되어 있다.
// -----------------------------------------------------------
Gaudi::Property<bool> m_doBirk{this, "DoBirk", true};
// -----------------------------------------------------------

// 현재 기본 상수, Birks Law의 상수는 m_birk1과 m_birk2로 정의되어 있으며,
// m_birk1은 0.02002 g/(MeV*cm^2)로 설정되어 있고, 
// m_birk2는 0.0 g/(MeV*cm^2)로 설정되어 있다. 
// 이 값들은 Geant4 10.6.p03 버전에 맞게 업데이트된 값이다. 
// -----------------------------------------------------------
Gaudi::Property<double> m_birk1{
    this, 
    "birk1",
    0.02002 * CLHEP::g / (CLHEP::MeV * CLHEP::cm2),
    "value updated for G4 10.6.p03"
};

Gaudi::Property<double> m_birk2{
    this, 
    "birk2",
    0.0 * CLHEP::g / (CLHEP::MeV * CLHEP::cm2) 
        * CLHEP::g / (CLHEP::MeV * CLHEP::cm2),
    "value updated for G4 10.6.p03"
};
// -----------------------------------------------------------