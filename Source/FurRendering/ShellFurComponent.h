// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShellFurComponent.generated.h"


UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class FURRENDERING_API UShellFurComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UShellFurComponent();

	UFUNCTION(BlueprintCallable, CallInEditor, Category="Shells")
	void BuildShells();

	UFUNCTION(BlueprintCallable, CallInEditor, Category="Shells")
	void ClearShells();

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	UFUNCTION()
	UStaticMeshComponent* GetOwnerMesh();

	UPROPERTY(EditAnywhere, Category = "Shells")
	UStaticMeshComponent* TargetMesh = nullptr;

	UPROPERTY(EditAnywhere, Category = "Shells")
	int32 ShellCount = 8;
	
	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float ShellStep = 0.2f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float UVScale = 3.0f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float FurSpecularStrength = 0.2f;
	
	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float FurDiffuseStrength = 0.25f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float FurRootDarken = 0.25f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	FLinearColor FurBaseColor = FLinearColor(0.06f, 0.03f, 0.025f, 1.0f);
	
	UPROPERTY(EditAnywhere, Category = "Shell Fur")
	FLinearColor FurSpecColor = FLinearColor(0.15f, 0.07f, 0.04f, 1.0f);

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> ShellLayers;
};
