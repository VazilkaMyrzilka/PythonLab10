
# 1. Створення CSV-файлу енергоспоживання стійок (power_rack.csv)
csv_content = """Timestamp,Voltage_V,Current_A,Frequency_Hz
2026-08-30 15:00:01,220.0,14.5,50.0
2026-08-30 15:00:02,222.5,17.2,50.0
2026-08-30 15:00:03,219.0,15.8,50.0
2026-08-30 15:00:04,221.0,18.5,50.0
2026-08-30 15:00:05,218.5,12.0,50.0
2026-08-30 15:00:06,223.0,16.5,50.0
"""

with open("power_rack.csv", "w", encoding="utf-8") as f:
    f.write(csv_content.strip())

# 2. Створення бінарного файлу прошивки (firmware_sample.bin)
# Сигнатура 'RACK' (0x52, 0x41, 0x43, 0x34) + Версія v1.2 (0x01, 0x02) + Корисне навантаження (Payload)
binary_payload = bytes([0x52, 0x41, 0x43, 0x34, 0x01, 0x02, 0xAA, 0xBB, 0xCC, 0xDD])

with open("firmware_sample.bin", "wb") as f:
    f.write(binary_payload)

print("Файли power_rack.csv та firmware_sample.bin успішно створено!")
