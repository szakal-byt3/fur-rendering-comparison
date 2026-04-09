// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShellFurComponent.generated.h"


UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class FURRENDER_API UShellFurComponent : public UActorComponent
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
	TObjectPtr<UStaticMeshComponent> TargetMesh = nullptr;

	UPROPERTY(EditAnywhere, Category = "Shells")
	int32 ShellCount = 8;
	
	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float ShellStep = 1.0f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	TObjectPtr<UMaterialInterface> ShellMaterial = nullptr;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float UVScale = 3.0f;

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> ShellLayers;
};
