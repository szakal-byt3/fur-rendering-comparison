#include "InstancedShellFurComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/StaticMeshComponent.h"

UInstancedShellFurComponent::UInstancedShellFurComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UInstancedShellFurComponent::BeginPlay()
{
	Super::BeginPlay();
	BuildShells();
}

void UInstancedShellFurComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

UStaticMeshComponent* UInstancedShellFurComponent::GetOwnerMesh() const
{
	if (const TObjectPtr<AActor> Owner = GetOwner())
	{
		return Owner->FindComponentByClass<UStaticMeshComponent>();
	}

	return nullptr;
}

void UInstancedShellFurComponent::GetOrCreateShellInstances()
{
	TObjectPtr<AActor> Owner = GetOwner();
	TObjectPtr<UStaticMeshComponent> OwnerMeshComponent = GetOwnerMesh();
	TObjectPtr<UStaticMesh> OwnerStaticMesh = OwnerMeshComponent ? OwnerMeshComponent->GetStaticMesh() : nullptr;

	if (!Owner || !OwnerMeshComponent || !OwnerStaticMesh)
	{
		UE_LOG(LogTemp, Warning, TEXT("InstancedShellFurComponent: Missing owner, static mesh component, or static mesh. Shells cannot be created."));
		return;
	}

	// Set ISM properties similar to ShellFurComponent's setup
	if (!ShellISM)
	{
		// Create ISM component for shells -- only one component needed compared to ShellFurComponent which creates one static mesh component per shell
		ShellISM = NewObject<UInstancedStaticMeshComponent>(Owner, TEXT("ShellISM"));
		ShellISM->SetupAttachment(OwnerMeshComponent);
		ShellISM->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		ShellISM->SetCastShadow(false);
		ShellISM->SetMobility(OwnerMeshComponent->Mobility);

		// Have to replace the per-shell custom data with per-instance custom data for ISM, 
		// so we set up 2 floats for shell index and shell offset 
		ShellISM->NumCustomDataFloats = 2;

		Owner->AddInstanceComponent(ShellISM);
		ShellISM->RegisterComponent();
	}

	ShellISM->SetStaticMesh(OwnerStaticMesh);
}

void UInstancedShellFurComponent::ConfigureShellMaterial()
{
	if (!ShellISM)
	{
		return;
	}

	if (!ShellMaterial)
	{
		ShellMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/M_InstancedShellFur.M_InstancedShellFur"));
	}

	// Create MID for shell material and set parameters
	if (TObjectPtr<UMaterialInstanceDynamic> MID = ShellISM->CreateDynamicMaterialInstance(0, ShellMaterial)) {
		MID->SetScalarParameterValue(TEXT("ShellCount"), ShellCount);
		MID->SetScalarParameterValue(TEXT("UVScale"), UVScale);
		MID->SetScalarParameterValue(TEXT("SpecularStrength"), FurSpecularStrength);
		MID->SetScalarParameterValue(TEXT("DiffuseStrength"), FurDiffuseStrength);
		MID->SetScalarParameterValue(TEXT("RootDarken"), FurRootDarken);
		MID->SetVectorParameterValue(TEXT("FurAlbedo"), FurBaseColor);
		MID->SetVectorParameterValue(TEXT("SpecularColor"), FurSpecColor);
		ShellISM->SetMaterial(0, MID);
	}
}

void UInstancedShellFurComponent::ClearShells()
{
	if (ShellISM)
	{
		ShellISM->ClearInstances();
	}
}

void UInstancedShellFurComponent::BuildShells()
{
	GetOrCreateShellInstances();
	ClearShells();
	ConfigureShellMaterial();

	for (int32 i = 0; i < ShellCount; i++)
	{
		int32 InstanceIndex = ShellISM->AddInstance(FTransform::Identity);
		ShellISM->SetCustomDataValue(InstanceIndex, 0, static_cast<float>(i), false);
		ShellISM->SetCustomDataValue(InstanceIndex, 1, static_cast<float>((i + 1) * ShellStep), false);
	}

	ShellISM->MarkRenderStateDirty();
}