// Fill out your copyright notice in the Description page of Project Settings.


#include "ShellFurComponent.h"

// Sets default values for this component's properties
UShellFurComponent::UShellFurComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = true;

	// ...
}


// Called when the game starts
void UShellFurComponent::BeginPlay()
{
	Super::BeginPlay();

	BuildShells();
	
}


// Called every frame
void UShellFurComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// ...
}

// Gets mesh of actor object that owns this component
UStaticMeshComponent* UShellFurComponent::GetOwnerMesh()
{
    if (AActor* Owner = GetOwner())
    {
        return Owner->FindComponentByClass<UStaticMeshComponent>();
    }

    return nullptr;
}


// Removes existing shells
void UShellFurComponent::ClearShells()
{
	AActor* Owner = GetOwner();
	for (UStaticMeshComponent* Shell : ShellLayers)
	{
		if (Shell != nullptr)
		{
			Shell->DestroyComponent();
			Owner->RemoveInstanceComponent(Shell);
		}
	}
}


// Creates shells by duplicating base mesh
void UShellFurComponent::BuildShells()
{
	ClearShells();
	AActor* Owner = GetOwner();
	UStaticMeshComponent* OwnerMesh = GetOwnerMesh();


	for (int32 i = 0; i < ShellCount; i++)
	{
		FName Name = *FString::Printf(TEXT("Shell_%d"), i);
		TObjectPtr<UStaticMeshComponent> Shell = NewObject<UStaticMeshComponent>(Owner, Name);
		
		// Attaches shell to the owner mesh and sets up properties
		Shell->SetupAttachment(OwnerMesh);
		Shell->SetStaticMesh(OwnerMesh->GetStaticMesh());
		Shell->SetCastShadow(false);
		Shell->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		if (ShellMaterial == nullptr)
		{
			ShellMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/M_ShellFur.M_ShellFur"));
		}
		Shell->SetMaterial(0, ShellMaterial);

		Owner->AddInstanceComponent(Shell);
		Shell->RegisterComponent();

		// Sends parameters to the material to control shell offset and UV scaling
		if (UMaterialInstanceDynamic* MID = Shell->CreateAndSetMaterialInstanceDynamic(0))
		{
			MID->SetScalarParameterValue(TEXT("ShellIndex"), static_cast<float>(i));
			MID->SetScalarParameterValue(TEXT("ShellCount"), static_cast<float>(ShellCount));
			MID->SetScalarParameterValue(TEXT("ShellOffset"), (i + 1) * ShellStep);
			MID->SetScalarParameterValue(TEXT("UVScale"), UVScale);
			MID->SetScalarParameterValue(TEXT("SpecularStrength"), FurSpecularStrength);
			MID->SetScalarParameterValue(TEXT("DiffuseStrength"), FurDiffuseStrength);
			MID->SetScalarParameterValue(TEXT("RootDarken"), FurRootDarken);
			MID->SetVectorParameterValue(TEXT("FurAlbedo"), FurBaseColor);
			MID->SetVectorParameterValue(TEXT("SpecularColor"), FurSpecColor);
		}
		
		ShellLayers.Add(Shell);
	}
}

