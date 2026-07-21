// SND@LHC의 MuFilter.h에서 Birks Law 관련 부분만 가져온 코드입니다.
// 실행용이 아닌, 기록용 코드입니다. 실제로는 SND@LHC의 MuFilter.cxx와 MuFilter.h를 참고하시기 바랍니다.

// MuFilter.h 클래스 정의 (25행)
// MuFilter 클래스는 FairDetector를 상속받아 Muon Filter 검출기를 나타냅니다. 
// 이 클래스는 MuFilter geometry 생성, sensitive volume 등록, 
// Monte Carlo step 처리, energy deposit 누적,
// 또한, Birks Law 관련 설정을 위한 구성 매개변수를 설정하고 가져오는 메서드도 포함되어 있습니다.
// ------------------------------------------------------------
class MuFilter : public FairDetector
// ------------------------------------------------------------


// ProcessHits() 선언 (53-54행)
// sensitive volume 안에서 Monte Carlo step이 발생할 때마다 호출된다.
// Birks correction은 step-by-step correction이므로 이 함수의 실행 흐름 안에 들어가야 한다.
// ------------------------------------------------------------
/**  Method called for each step during simulation (see FairMCApplication::Stepping()) */
virtual Bool_t ProcessHits( FairVolume* v=0);
// ------------------------------------------------------------


// AddHit() 선언 (67-68행)
// 이 함수는 계산이 끝난 energy loss를 MuFilterPoint로 저장한다.
// ------------------------------------------------------------
MuFilterPoint* AddHit(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
		Double_t time, Double_t length, Double_t eLoss, Int_t pdgCode);
// ------------------------------------------------------------
// Double_t eloss가 최종 저장되는 에너지이다.
// Birks correction을 적용하면 이 값은 더 이상 raw deposited energy가 아니라
// accumulated visible energy가 된다.


// track 정보 저장 변수 (88-95행)
// -------------------------------------------------------------
/** Track information to be stored until the track leaves the active volume. */
Int_t          fTrackID;           //!  track index
Int_t          fVolumeID;          //!  volume id
TLorentzVector fPos;               //!  position at entrance
TLorentzVector fMom;               //!  momentum at entrance
Double32_t     fTime;              //!  time
Double32_t     fLength;            //!  length
Double32_t     fELoss;             //!  energy loss
// -------------------------------------------------------------
// Birks 구현에서 가장 중요한 변수는 fELoss이다.
// 현재 의미는 "step에서 발생한 energy loss"이지만, Birks correction을 적용하면
// "step에서 발생한 visible energy"가 된다.
// Double32_t fLength; 라는 이름 때문에 Birks 계산에 사용할 수 있을 것처럼 보이지만 그렇지 않다.
// fLength에는 track이 volume에 들어온 순간의 gMC->TrackLength()가 저장된다.
// 이는 current step length가 아니라 track의 누적 이동 거리이다.
// Birks 식의 delta_x에는 반드시 gMC->TrackStep()을 사용해야 한다.


// ROOT class version (84행)
// -------------------------------------------------------------
ClassDef(MuFilter,4)
// -------------------------------------------------------------
// ROOT dictionary와 serialization을 위한 class version이다.
// 함수 선언만 추가하고 persistent data member를 추가하지 않는다면 보통 version을 변경할 필요는 없다.
// 하지만 새 kB member variable 등을 클래스에 저장하도록 설계한다면
// ROOT dictionary 정책을 supervisor와 확인하는 것이 안전하다.