#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "InstancedShellFurComponent.generated.h"

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class FURRENDERING_API UInstancedShellFurComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UInstancedShellFurComponent();

	UFUNCTION(BlueprintCallable, CallInEditor, Category="Shells")
	void BuildShells();

	UFUNCTION(BlueprintCallable, CallInEditor, Category="Shells")
	void ClearShells();

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	UStaticMeshComponent* GetOwnerMesh() const;

protected:
	UPROPERTY(EditAnywhere, Category="Shells")
	TObjectPtr<UStaticMeshComponent> TargetMesh = nullptr;

	UPROPERTY(EditAnywhere, Category="Shells")
	int32 ShellCount = 8;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	TObjectPtr<UMaterialInterface> ShellMaterial = nullptr;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float ShellStep = 0.2f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float UVScale = 1.0f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float FurSpecularStrength = 0.2f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float FurDiffuseStrength = 0.25f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	float FurRootDarken = 0.25f;

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	FLinearColor FurBaseColor = FLinearColor(0.365f, 0.265f, 0.125f, 1.0f);

	UPROPERTY(EditAnywhere, Category="Shell Fur")
	FLinearColor FurSpecColor = FLinearColor(0.62f, 0.45f, 0.35f, 1.0f);

public:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UPROPERTY()
	TObjectPtr<UInstancedStaticMeshComponent> ShellISM = nullptr;

	UFUNCTION()
	void GetOrCreateShellInstances();

	UFUNCTION()
	void ConfigureShellMaterial();

};