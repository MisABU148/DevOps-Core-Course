package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
	"strings"
	"time"
)

// Структуры как в Python
type ServiceInfo struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

type SystemInfo struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	PythonVersion   string `json:"python_version"`
}

type RuntimeInfo struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

type EndpointInfo struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
	Service       string `json:"service"`
	Version       string `json:"version"`
}

type MainResponse struct {
	Service   ServiceInfo    `json:"service"`
	System    SystemInfo     `json:"system"`
	Runtime   RuntimeInfo    `json:"runtime"`
	Request   RequestInfo    `json:"request"`
	Endpoints []EndpointInfo `json:"endpoints"`
}

var startTime time.Time

func init() {
	startTime = time.Now()
}

func getUptime() (seconds int64, human string) {
	delta := time.Since(startTime)
	seconds = int64(delta.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	if hours > 0 {
		hourWord := "hour"
		if hours != 1 {
			hourWord = "hours"
		}
		minuteWord := "minute"
		if minutes != 1 {
			minuteWord = "minutes"
		}
		human = fmt.Sprintf("%d %s, %d %s", hours, hourWord, minutes, minuteWord)
	} else {
		minuteWord := "minute"
		if minutes != 1 {
			minuteWord = "minutes"
		}
		human = fmt.Sprintf("%d %s", minutes, minuteWord)
	}

	return seconds, human
}

func getClientIP(r *http.Request) string {
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		parts := strings.Split(forwarded, ",")
		if len(parts) > 0 {
			return strings.TrimSpace(parts[0])
		}
	}

	if realIP := r.Header.Get("X-Real-IP"); realIP != "" {
		return realIP
	}

	return r.RemoteAddr
}

func formatTimestamp(t time.Time) string {
	return t.UTC().Format("2006-01-02T15:04:05.000Z")
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}

	hostname, _ := os.Hostname()
	uptimeSeconds, uptimeHuman := getUptime()
	clientIP := getClientIP(r)
	userAgent := r.Header.Get("User-Agent")
	if userAgent == "" {
		userAgent = "unknown"
	}

	response := MainResponse{
		Service: ServiceInfo{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go",
		},
		System: SystemInfo{
			Hostname:        hostname,
			Platform:        runtime.GOOS,
			PlatformVersion: runtime.Version(),
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
			PythonVersion:   "3.12.0 (emulated)",
		},
		Runtime: RuntimeInfo{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   formatTimestamp(time.Now()),
			Timezone:      "UTC",
		},
		Request: RequestInfo{
			ClientIP:  clientIP,
			UserAgent: userAgent,
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []EndpointInfo{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}

	log.Printf("GET / from %s", clientIP)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()

	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     formatTimestamp(time.Now()),
		UptimeSeconds: uptimeSeconds,
		Service:       "devops-info-service",
		Version:       "1.0.0",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "5001" // Другой порт, чтобы не конфликтовать с Python
	}

	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	log.Printf("Starting Go service on port %s", port)
	log.Printf("Endpoints:")
	log.Printf("  http://localhost:%s/", port)
	log.Printf("  http://localhost:%s/health", port)

	log.Fatal(http.ListenAndServe(":"+port, nil))
}