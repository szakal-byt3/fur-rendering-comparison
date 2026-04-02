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


// Unregisters existing shells
void UShellFurComponent::ClearShells()
{
	for (UStaticMeshComponent* Shell : ShellLayers)
	{
		Shell->DestroyComponent();
	}
}


// Creates shells by duplicating base mesh
void UShellFurComponent::BuildShells()
{
	ClearShells();
	UStaticMeshComponent* OwnerMesh = GetOwnerMesh();


	for (int32 i = 0; i < ShellCount; i++)
	{
		FName Name = *FString::Printf(TEXT("Shell_%d"), i);
		TObjectPtr<UStaticMeshComponent> Shell = NewObject<UStaticMeshComponent>(OwnerMesh, Name);
		
		Shell->SetupAttachment(OwnerMesh);
		Shell->SetStaticMesh()
	}
}
