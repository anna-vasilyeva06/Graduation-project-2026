"""
Скрипт предобучения ML-модели здоровья системы.

Запускайте на этапе разработки или перед сборкой приложения:
  python train_ml_health.py

Создаёт/перезаписывает core/ml_health_model.json. При поставке приложения
включайте этот файл в дистрибутив — тогда у пользователя модель уже будет
работать без сбора 25+ примеров.
"""
import sys
import os

# чтобы импортировать core из корня проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ml_health import (
    generate_synthetic_samples,
    train_model,
    save_model,
    MODEL_PATH,
    MIN_SAMPLES_TO_TRAIN,
)

NUM_SAMPLES = 500


def main():
    print("Генерация синтетических примеров...")
    samples = generate_synthetic_samples(NUM_SAMPLES)
    print(f"  Сгенерировано {len(samples)} примеров.")

    print("Обучение модели...")
    model = train_model(samples)
    if model is None:
        print("  Ошибка: модель не обучена (нужно минимум {} примеров).".format(MIN_SAMPLES_TO_TRAIN))
        return 1

    save_model(model)
    print(f"  Модель сохранена: {MODEL_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
