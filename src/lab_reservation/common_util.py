class CommonUtil:
    @staticmethod
    def empty(value):
        return value is None or value.strip() == ""

    @staticmethod
    def calculate_fee(user_type, equipment_type, start_at, end_at, emergency):
        minutes = int((end_at - start_at).total_seconds() // 60)
        units = (minutes + 29) // 30

        if equipment_type == "LASER_CUTTER":
            hourly_rate = 1200
        elif equipment_type == "GPU_SERVER":
            hourly_rate = 2000
        elif equipment_type == "MOTION_CAPTURE":
            hourly_rate = 5000
        else:
            raise ValueError(f"unknown equipment type: {equipment_type}")

        if user_type == "STUDENT":
            multiplier = 0.5
        elif user_type == "STAFF":
            multiplier = 0.8
        elif user_type == "EXTERNAL":
            multiplier = 1.5
        else:
            raise ValueError(f"unknown user type: {user_type}")

        result = int(hourly_rate * (units / 2.0) * multiplier)
        if emergency:
            result += 2000
        return result

    @staticmethod
    def equipment_label(equipment_type):
        if equipment_type == "LASER_CUTTER":
            return "レーザーカッター"
        if equipment_type == "GPU_SERVER":
            return "GPUサーバ"
        if equipment_type == "MOTION_CAPTURE":
            return "モーションキャプチャ"
        return "不明な設備"

    @staticmethod
    def user_label(user_type):
        if user_type == "STUDENT":
            return "学生"
        if user_type == "STAFF":
            return "教職員"
        if user_type == "EXTERNAL":
            return "学外利用者"
        return "不明な利用者"
