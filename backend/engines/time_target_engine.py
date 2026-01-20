class TimeTargetValidator:
    def validate(self, distance, time_left, avg_speed):
        required_time = distance / avg_speed

        if required_time > time_left:
            return "INVALID"

        if required_time > time_left * 0.7:
            return "DELAYED"

        return "ACTIVE"
