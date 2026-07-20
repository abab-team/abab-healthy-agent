const { withAndroidManifest } = require("@expo/config-plugins");

/**
 * The HTTP QA build intentionally targets a private test server without TLS.
 * Expo SDK 54 does not map the legacy app.json property to the Android
 * manifest, so make the Android network policy explicit at prebuild time.
 */
module.exports = function withAndroidCleartextTraffic(config) {
  return withAndroidManifest(config, (nextConfig) => {
    const application = nextConfig.modResults.manifest.application?.[0];
    if (!application) {
      throw new Error("AndroidManifest is missing its application node.");
    }

    application.$ = application.$ ?? {};
    application.$["android:usesCleartextTraffic"] = "true";
    return nextConfig;
  });
};
