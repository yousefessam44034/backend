pipeline {
    agent any

    stages {
        stage('Print Current Directory') {
            steps {
                bat 'cd C:/Users/youse/Desktop/S5_20206163_20206155_20196084_TA-ESRAA/Clinic-Reservation-System && cd backend && echo %cd%'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    bat 'docker build --pull --rm -f "Clinic-Reservation-System//backend//dockerfile" -t backend:latest "Clinic-Reservation-System/backend"'
                }
            }
        }
    }
}
