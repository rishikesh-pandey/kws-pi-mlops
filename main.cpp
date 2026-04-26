#include <stdio.h>
#include "pico/stdlib.h"
#include "edge-impulse-sdk/classifier/ei_run_classifier.h"

// Buffer for 1 second of 16kHz audio
float features[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];

// Callback for Edge Impulse to read the audio array
int raw_feature_get_data(size_t offset, size_t length, float *out_ptr) {
    memcpy(out_ptr, features + offset, length * sizeof(float));
    return 0;
}
// --------------------------------------------------------
// OTA UPDATE STUBS (To be filled in later)
// --------------------------------------------------------
void check_for_ota_updates() {
    printf("🌐 Connecting to GitHub API...\n");
    // TODO: HTTP GET request to GitHub Releases
    // TODO: If new version > current version, download to Partition B
    // TODO: Set Bootloader flag and reboot
}

int main() {
    stdio_init_all();
    
    // Give the USB serial port a second to connect
    sleep_ms(2000); 
    printf("🚀 Microcontroller KWS Booted. Partition A Active.\n");

    uint32_t loop_counter = 0;

    while (true) {
        printf("🎤 Recording audio... (Simulated)\n");
        // TODO: Read from physical I2S or analog microphone here
        
        // Fill array with dummy data for compilation testing
        for(int i = 0; i < EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE; i++) {
            features[i] = 0.0f; 
        }

        signal_t signal;
        signal.total_length = EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE;
        signal.get_data = &raw_feature_get_data;

        ei_impulse_result_t result = {0};
        EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);

        if (res == EI_IMPULSE_OK) {
            printf("📊 Predictions:\n");
            for (uint16_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
                printf("  %s: %.5f\n", result.classification[i].label, result.classification[i].value);
            }
        }

        // Simulate a 24-hour polling cycle (Checking every 10 loops for testing)
        loop_counter++;
        if (loop_counter % 10 == 0) {
            printf("⏰ 24-Hour Timer Triggered. Checking for firmware updates...\n");
            check_for_ota_updates();
        }

        sleep_ms(1000);
    }
    return 0;
}