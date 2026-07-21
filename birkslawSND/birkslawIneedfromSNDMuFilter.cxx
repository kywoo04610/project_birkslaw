// SND@LHC의 MuFilter.cxx에서 Birks Law 관련 부분만 가져온 코드입니다.
// 실행용이 아닌, 기록용 코드입니다. 실제로는 SND@LHC의 MuFilter.cxx와 MuFilter.h를 참고하시기 바랍니다.

// 필요한 include (7행)
// MuFilter 클래스 선언을 불러온다.
// ------------------------------------------------------------
#include "MuFilter.h"
// ------------------------------------------------------------


// hit class (8행)
// 최종 energy deposit을 저장할 MuFilterPoint을 정의한다.
// ------------------------------------------------------------
#include "MuFilterPoint.h"
// ------------------------------------------------------------


// TVirtualMC (14행)
// ------------------------------------------------------------
#include "TVirtualMC.h"
// ------------------------------------------------------------
// 이 include 때문에 전역 객체 gMC를 사용할 수 있다.
// gMC가 제공하는 Birks 관련 정보는 다음과 같다.
// 현재 step energy deposit ; gMC->Edep()
// 현재 step length ; gMC->TrackStep()
// 현재 입자 전하 ; gMC->TrackCharge()
// 현재 material 정보 ; gMC->CurrentMaterial(...)
// 현재 volume ; gMC->CurrentVolID(...)
// track 총 이동 길이 ; gMC->TrackLength()


// material 및 medium (17-18행)
// 현재 geometry material과 tracking medium을 다루는 클래스이다.
// Birks 구현에서는 density를 gMC->CurrentMaterial()로 가져오는 것이 가장 직접적이지만,
// 필요하면 TGeoMaterial을 통한 cross-check도 가능하다.
// ------------------------------------------------------------
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
// ------------------------------------------------------------


// ShipUnit (40행)
// SND simulation의 단위 정의를 제공한다.
// Birks 상수는 MeV와 cm 기준이므로 단위가 필요하다.
// ------------------------------------------------------------
#include "ShipUnit.h"
// ------------------------------------------------------------


// ShipUnit namespace (52행)
// 이 선언 때문에 함수 안에서 ShipUnit::MeV 대신 간단히 MeV라고 쓸 수 있다.
// ------------------------------------------------------------
using namespace ShipUnit;
// ------------------------------------------------------------


// 생성자: fELoss 초기값
// 기본 생성자 (54-68행)
// ------------------------------------------------------------
MuFilter::MuFilter()
: FairDetector("MuonFilter", "",kTRUE),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
eventHeader(0),
last_run_time(-1),
last_run_pos(-1),
last_time_alignment_tag(""),
alignment_init(false),
fMuFilterPointCollection(new TClonesArray("MuFilterPoint"))
{
}
// ------------------------------------------------------------

// 인자를 받는 생성자 (72-86행)
// ------------------------------------------------------------
MuFilter::MuFilter(const char* name, Bool_t Active,const char* Title)
: FairDetector(name, true, kMuFilter),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
eventHeader(0),
last_run_time(-1),
last_run_pos(-1),
last_time_alignment_tag(""),
alignment_init(false),
fMuFilterPointCollection(new TClonesArray("MuFilterPoint"))
{
}
// ------------------------------------------------------------
// 객체가 생성될 때 fELoss의 초기값은 -1이다.
// 하지만 실제 track이 sensitive volume에 들어오면 ProcessHits()에서 0으로 초기화하므로,
// Birks 계산은 생성자의 -1 값에 적용되지 않는다.


// Scintillator material 정의 (129-136행)
// ------------------------------------------------------------
//Materials 
InitMedium("iron");
TGeoMedium *Fe = 
    gGeoManager->GetMedium("iron");

InitMedium("aluminium");
TGeoMedium *Al =
    gGeoManager->GetMedium("aluminium");

InitMedium("polyvinyltoluene");
TGeoMedium *Scint =
    gGeoManager->GetMedium("polyvinyltoluene");
// ------------------------------------------------------------
// MuFilter scintillator는 polyvinyltoluene medium을 사용한다.
// EJ-200도 PVT 기반 plastic scintillator이다.
// 다만 이 파일은 material 이름만 가져오며, 
// PVT density, 수소 및 탄소 조성, radiation length의 정보는 정의하지 않는다.


// Sensitive scintillator volume
// ProcessHits()는 모든 geometry volume에서 호출되는 것이 아니라
// AddSensitiveVolume()으로 등록된 volume에서 호출된다.
// Veto bars (222-230행)
// ------------------------------------------------------------
//Veto bars
TGeoVolume *volVetoBar = 
    gGeoManager->MakeBox(
        "volVetoBar",
        Scint,
        fVetoBarX/2.,
        fVetoBarY/2., 
        fVetoBarZ/2.
    );
// 3rd plane
TGeoVolume *volVetoBar_ver = 
    gGeoManager->MakeBox(
        "volVetoBar_ver",
        Scint,
        fVeto3BarX/2.,
        fVeto3BarY/2., 
        fVeto3BarZ/2.
    );

volVetoBar->SetLineColor(kRed-3);
AddSensitiveVolume(volVetoBar);

volVetoBar_ver->SetLineColor(kRed-3);
AddSensitiveVolume(volVetoBar_ver);
// ------------------------------------------------------------
// 두 volume 모두 Scint, 즉 PVT를 사용한다.

// Upstream bars (340-342행)
// ------------------------------------------------------------
TGeoVolume *volMuUpstreamBar = 
    gGeoManager->MakeBox(
        "volMuUpstreamBar",
        Scint,
        fUpstreamBarX/2, 
        fUpstreamBarY/2, 
        fUpstreamBarZ/2
    );

volMuUpstreamBar->SetLineColor(kBlue+2);
AddSensitiveVolume(volMuUpstreamBar);
// ------------------------------------------------------------
// 프로젝트 verification에서 보는 US1, US2, US3의 bar들은 이 volume에 해당한다.

// Downstream vertical bars (397-399행)
// ------------------------------------------------------------
TGeoVolume *volMuDownstreamBar_ver = 
    gGeoManager->MakeBox(
        "volMuDownstreamBar_ver",
        Scint,
        fDownstreamBarX_ver/2, 
        fDownstreamBarY_ver/2, 
        fDownstreamBarZ/2
    );
volMuDownstreamBar_ver->SetLineColor(kViolet-2);
AddSensitiveVolume(volMuDownstreamBar_ver);
// ------------------------------------------------------------
// 현재 MuFilter::ProcessHits()가 호출되는 sensitive detector volume은 
// 모두 Scint medium으로 만들어진 PVT bar이다.
// 이 점 때문에 "scintillator 자체에서만 Birks 적용"이라는 조건은 구조적으로 만족된다.
// 그래도 helper function의 안전성을 위해 current material의 이름이나 density를 확인할 수 있다.


// 핵심 함수 : ProcessHits()
// ------------------------------------------------------------
Bool_t  MuFilter::ProcessHits(FairVolume* vol)
{
	/** This method is called from the MC stepping */
// ------------------------------------------------------------
// 매 step 호출되는 함수이다.

// ------------------------------------------------------------
	//Set parameters at entrance of volume. Reset ELoss.
	if ( gMC->IsTrackEntering() ) 
	{
		fELoss  = 0.;
		fTime   = gMC->TrackTime() * 1.0e09;
		fLength = gMC->TrackLength();
		gMC->TrackPosition(fPos);
		gMC->TrackMomentum(fMom);
	}
// ------------------------------------------------------------
// fELoss는 현재 bar에서 누적할 energy 초기화
// fTime은 bar 진입 시간, ns
// fLength는 진입 시점까지의 track 누적 길이
// fPos는 bar 진입 위치
// fMom은 bar 진입 운동량
// Birks 관련 핵심은 fELoss = 0.;이다.
// 이후 모든 step의 corrected energy가 이 변수에 더해진다.

// ------------------------------------------------------------
	// Sum energy loss for all steps in the active volume
	fELoss += gMC->Edep();
// ------------------------------------------------------------
// 실제 Birks 적용 대상이다.

// ------------------------------------------------------------
	// Create MuFilterPoint at exit of active volume
	if ( gMC->IsTrackExiting()    ||
			gMC->IsTrackStop()       || 
			gMC->IsTrackDisappeared()   ) {
// ------------------------------------------------------------
// 위 조건 중 하나가 발생하면 현재 bar에서 energy accumulation을 종료한다.
// track이 volume 밖으로 나가거나, 
// track이 volume 안에서 정지하거나, 
// track이 interaction이나 decay로 사라지면 종료한다.
// Birks correction은 이 시점에 한 번 적용하는 것이 아니라, 
// 여기까지 도달하기 전의 매 step에서 이미 적용되어 있어야 한다.

// Track ID와 volume ID
// ------------------------------------------------------------
		fTrackID  = 
            gMC->GetStack()->GetCurrentTrackNumber();

		gMC->CurrentVolID(fVolumeID);
// ------------------------------------------------------------
// 현재 track 및 detector volume의 ID를 얻는다.
// Birks 계산에는 직접 필요하지 않지만, 최종 hit이 어느 track과 bar에 속하는지 저장하는 데 사용된다.

// Zero-energy hit 제거
// ------------------------------------------------------------
		if (fELoss == 0. ) { 
            return kFALSE; 
        }
// ------------------------------------------------------------
// 한 bar에서 최종 누적 visible energy가 0이면 hit을 만들지 않는다.
// Birks correction은 양의 raw energy를 완전히 0으로 만들지는 않으므로 
// 일반적인 charged-particle hit에는 영향이 없다.

// PDG code
// 입자의 PDG code를 가져온다.
// Birks 적용 조건의 charged/neutral 여부는 PDG code를 직접 해석하기 보다
// gMC->TrackCharge()를 사용하는 것이 더 단순하고 정확하다.
// ------------------------------------------------------------
		TParticle* p=
            gMC->GetStack()->GetCurrentTrack();

		Int_t pdgCode = 
            p->GetPdgCode();
// ------------------------------------------------------------

// 평균 hit position
// ------------------------------------------------------------
		TLorentzVector Pos; 
		gMC->TrackPosition(Pos); 
		Double_t xmean = (fPos.X()+Pos.X())/2. ;
		Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
		Double_t zmean = (fPos.Z()+Pos.Z())/2. ;
// ------------------------------------------------------------
// volume 진입 위치와 종료 위치의 평균을 hit position으로 사용한다.
// Birks correction과 직접 관계는 없다.

// AddHit() 호출
// ------------------------------------------------------------
		AddHit(
            fTrackID,
            fVolumeID, 
            TVector3(xmean, ymean,  zmean),
			TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), 
            fTime, 
            fLength,
			fELoss, 
            pdgCode
        );
// ------------------------------------------------------------
// 여기서 fELoss가 최종 MuFilterPoint에 전달된다.
// 따라서 Birks 적용 후에는 fELoss의 의미가 다음처럼 바뀐다.
// raw deposited energy -> visible-equivalent energy
// AddHit() 자체는 수정할 필요가 없다.

// ------------------------------------------------------------
		// Increment number of muon det points in TParticle
		ShipStack* stack = (ShipStack*) gMC->GetStack();
		stack->AddPoint(kMuFilter);
	}   

	return kTRUE;
}
// ------------------------------------------------------------

// AddHit() 구현
// ------------------------------------------------------------
MuFilterPoint* MuFilter::AddHit(
    Int_t trackID,
    Int_t detID,
    TVector3 pos, 
    TVector3 mom,
    Double_t time, 
    Double_t length,
    Double_t eLoss, 
    Int_t pdgCode
)
{
    TClonesArray& clref = 
        *fMuFilterPointCollection;

    Int_t size = 
        clref.GetEntriesFast();

    return new(clref[size]) MuFilterPoint(
        trackID,
        detID, 
        pos, 
        mom,
        time, 
        length, 
        eLoss, 
        pdgCode
    );
}
// ------------------------------------------------------------
// 전달받은 eLoss를 그대로 MuFilterPoint constructor에 넘긴다.
// 따라서 이 함수에도 Birks-specific code를 넣지 않는다.
// Birks correction을 여기서 적용하면 안 되는 이유는 step별 dE/dx 정보가 이미 사라졌기 때문이다.
