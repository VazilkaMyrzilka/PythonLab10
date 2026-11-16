"""
Лабораторна робота № 10.
Комплексний конвеєр файлового введення-виведення: обробка CSV,
бінарна верифікація сигнатур та персистентна серіалізація у JSON.
Освітній компонент: Програмування на Python.
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

# Константа 4-байтної магічної сигнатури бінарного образу ('RACK' у HEX)
FIRMWARE_MAGIC_HEADER = bytes([0x52, 0x41, 0x43, 0x34])


def process_csv_telemetry(input_csv_path: Path, output_csv_path: Path) -> dict:
    """
    Зчитує дані енергоспоживання стійок через csv.DictReader, фільтрує за критерієм
    струму фази (> 16 А), розраховує потужність та знаходить пікову активну потужність.
    """
    if not input_csv_path.exists():
        raise FileNotFoundError(f"Вхідний файл '{input_csv_path}' не знайдено.")

    total_records = 0
    valid_records = 0
    peak_power_watts = 0.0
    cleaned_rows = []

    with open(input_csv_path, mode="r", encoding="utf-8") as in_file:
        reader = csv.DictReader(in_file)

        for row in reader:
            total_records += 1
            voltage = float(row["Voltage_V"])
            current = float(row["Current_A"])
            freq = float(row["Frequency_Hz"])

            # Критерій валідності за Варіантом 12: Струм фази > 16 А
            if current > 16.0:
                valid_records += 1
                power_w = voltage * current
                
                # Знаходження пікової (максимальної) активної потужності
                if power_w > peak_power_watts:
                    peak_power_watts = power_w

                cleaned_rows.append({
                    "Timestamp": row["Timestamp"],
                    "Voltage_V": f"{voltage:.2f}",
                    "Current_A": f"{current:.2f}",
                    "Power_W": f"{power_w:.2f}",
                    "Frequency_Hz": f"{freq:.2f}"
                })

    # Запис відфільтрованих даних у новий файл
    if cleaned_rows:
        fieldnames = ["Timestamp", "Voltage_V", "Current_A", "Power_W", "Frequency_Hz"]
        with open(output_csv_path, mode="w", encoding="utf-8", newline="") as out_file:
            writer = csv.DictWriter(out_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)

    return {
        "total_read_rows": total_records,
        "valid_saved_rows": valid_records,
        "anomalous_rows_dropped": total_records - valid_records,
        "peak_active_power_watts": peak_power_watts
    }


def verify_binary_firmware(bin_path: Path) -> dict:
    """
    Здійснює низькорівневий аналіз бінарного образу прошивки:
    перевіряє магічну сигнатуру 0x52414334 ('RACK'), вилучає версію та розмір.
    """
    if not bin_path.exists():
        raise FileNotFoundError(f"Файл бінарного образу '{bin_path}' не знайдено.")

    with open(bin_path, mode="rb") as b_file:
        header = b_file.read(4)
        if header != FIRMWARE_MAGIC_HEADER:
            raise ValueError(
                f"Невідомий формат образу: сигнатура {header.hex().upper()} != {FIRMWARE_MAGIC_HEADER.hex().upper()}"
            )

        major_ver = int(b_file.read(1)[0])
        minor_ver = int(b_file.read(1)[0])

        current_pos = b_file.tell()
        file_size_bytes = b_file.seek(0, os.SEEK_END)
        payload_size = file_size_bytes - current_pos

    return {
        "magic_signature_hex": f"0x{header.hex().upper()}",
        "firmware_version": f"v{major_ver}.{minor_ver}",
        "total_image_size_bytes": file_size_bytes,
        "payload_size_bytes": payload_size,
        "is_signature_valid": True
    }


def export_system_snapshot(output_json_path: Path, csv_stats: dict, bin_stats: dict) -> None:
    """Серіалізує підсумковий стан системи у структурований JSON-документ."""
    snapshot_payload = {
        "station_metadata": {
            "facility_name": "Data Center Rack Power Monitoring",
            "snapshot_generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pipeline_version": "1.0.0"
        },
        "rack_telemetry_summary": csv_stats,
        "controller_firmware_audit": bin_stats
    }

    with open(output_json_path, mode="w", encoding="utf-8") as j_file:
        json.dump(snapshot_payload, j_file, indent=4, ensure_ascii=False)


def main() -> None:
    print("=" * 80)
    print(f"{'КОНВЕЄР ЕНЕРГОСПОЖИВАННЯ СТІЙОК ТА АУДИТУ ПРОШИВКИ':^80}")
    print("=" * 80)

    input_csv = Path("power_rack.csv")
    cleaned_csv = Path("cleaned_power_rack.csv")
    input_bin = Path("firmware_sample.bin")
    output_json = Path("rack_snapshot.json")

    t_start = time.perf_counter()

    # 1. Обробка CSV телеметрії стійок
    csv_metrics = process_csv_telemetry(input_csv, cleaned_csv)
    print(f"Обробка CSV успішна:")
    print(f"  Зчитано рядків:           {csv_metrics['total_read_rows']:>5d}")
    print(f"  Валідних рядків (>16А):   {csv_metrics['valid_saved_rows']:>5d}")
    print(f"  Відкинуто рядків:         {csv_metrics['anomalous_rows_dropped']:>5d}")
    print(f"  Пікова активна потужність:{csv_metrics['peak_active_power_watts']:>8.2f} Вт")
    print(f"  Файл збережено:           {cleaned_csv.name}")
    print("-" * 80)

    # 2. Аудит бінарного образу (сигнатура 'RACK')
    bin_metrics = verify_binary_firmware(input_bin)
    print(f"Аудит бінарного образу успішний:")
    print(f"  Магічна сигнатура:        {bin_metrics['magic_signature_hex']} (ASCII: 'RACK')")
    print(f"  Версія прошивки:          {bin_metrics['firmware_version']}")
    print(f"  Загальний розмір:         {bin_metrics['total_image_size_bytes']} байтів")
    print(f"  Розмір корисних даних:    {bin_metrics['payload_size_bytes']} байтів")
    print("-" * 80)

    # 3. Серіалізація у JSON
    export_system_snapshot(output_json, csv_metrics, bin_metrics)
    print(f"Підсумковий знімок стану збережено у JSON:")
    print(f"  Цільовий файл:            {output_json.name}")
    print("=" * 80)

    t_elapsed = time.perf_counter() - t_start
    print(f"Час виконання повного конвеєра: {t_elapsed * 1000:.3f} мс\n")


if __name__ == "__main__":
    main()