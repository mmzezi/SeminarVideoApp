package com.example.webviewapp

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    companion object {
        private const val URL = "http://10.0.2.2:5000/" // Example IP and port
        private const val ALLOWED_HOST = "10.0.2.2" // Trusted IP address
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val webView: WebView = findViewById(R.id.webview)
        val webSettings: WebSettings = webView.settings

        // Enable JavaScript with caution
        webSettings.javaScriptEnabled = true
        webSettings.safeBrowsingEnabled = true

        // Disable local file access for security
        webSettings.allowFileAccess = false
        webSettings.allowContentAccess = false

        // Secure WebViewClient
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                return request?.url?.host != ALLOWED_HOST
            }
        }

        webView.loadUrl(URL)
    }
}
