import { getCurrentUser, getToken } from "/static/js/auth.js";
import { getErrorMessage } from "/static/js/utils.js";

async function fetchJson(url) {
  const token = getToken();
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (response.status === 401) {
    window.location.href = "/login";
    return null;
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(getErrorMessage(error));
  }

  return response.json();
}

function formatDate(value) {
  return new Date(value).toLocaleDateString([], {
    month: "short",
    day: "numeric",
  });
}

function normalizeDate(value) {
  return new Date(value).toISOString().split("T")[0];
}

function round(value, digits = 1) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function linearRegression(points) {
  const n = points.length;
  if (n === 0) return { slope: 0, intercept: 0 };
  if (n === 1) return { slope: 0, intercept: points[0].y };

  const sumX = points.reduce((acc, point) => acc + point.x, 0);
  const sumY = points.reduce((acc, point) => acc + point.y, 0);
  const sumXY = points.reduce((acc, point) => acc + point.x * point.y, 0);
  const sumXX = points.reduce((acc, point) => acc + point.x * point.x, 0);

  const denominator = n * sumXX - sumX * sumX;
  if (denominator === 0) {
    return { slope: 0, intercept: sumY / n };
  }

  const slope = (n * sumXY - sumX * sumY) / denominator;
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

function kMeans(points, k = 3, maxIterations = 25) {
  if (points.length === 0) return { centroids: [], labels: [] };

  const initialCount = Math.min(k, points.length);
  let centroids = points.slice(0, initialCount).map((point) => [...point]);

  while (centroids.length < k) {
    centroids.push([...centroids[centroids.length - 1]]);
  }

  let labels = new Array(points.length).fill(0);

  for (let iteration = 0; iteration < maxIterations; iteration += 1) {
    let changed = false;

    for (let i = 0; i < points.length; i += 1) {
      let bestIndex = 0;
      let bestDistance = Infinity;

      for (let c = 0; c < centroids.length; c += 1) {
        const distance = Math.sqrt(
          points[i].reduce((acc, value, index) => acc + (value - centroids[c][index]) ** 2, 0),
        );

        if (distance < bestDistance) {
          bestDistance = distance;
          bestIndex = c;
        }
      }

      if (labels[i] !== bestIndex) {
        labels[i] = bestIndex;
        changed = true;
      }
    }

    const nextCentroids = centroids.map(() => []);
    const counts = centroids.map(() => 0);

    points.forEach((point, pointIndex) => {
      const label = labels[pointIndex];
      counts[label] += 1;
      point.forEach((value, featureIndex) => {
        nextCentroids[label][featureIndex] = (nextCentroids[label][featureIndex] || 0) + value;
      });
    });

    centroids = centroids.map((centroid, index) => {
      if (counts[index] === 0) return centroid;
      return centroid.map((_, featureIndex) => nextCentroids[index][featureIndex] / counts[index]);
    });

    if (!changed) break;
  }

  return { centroids, labels };
}

function labelCluster(centroid) {
  const [caloriesIn, caloriesBurned, sleepHours, netCalories] = centroid;
  if (netCalories <= 0 && caloriesBurned >= caloriesIn * 0.9 && sleepHours >= 7) return "Balanced";
  if (caloriesIn > caloriesBurned * 1.2 || netCalories > 250) return "Needs Attention";
  if (caloriesBurned >= caloriesIn && sleepHours >= 7) return "Active";
  return "Moderate";
}

function buildDailySeries(foodLogs, exerciseLogs, sleepLogs, weightLogs) {
  const days = new Map();

  const ensureDay = (date) => {
    if (!days.has(date)) {
      days.set(date, {
        date,
        caloriesIn: 0,
        caloriesBurned: 0,
        sleepHours: 0,
        sleepCount: 0,
        weight: null,
      });
    }
    return days.get(date);
  };

  foodLogs.forEach((log) => {
    ensureDay(normalizeDate(log.date)).caloriesIn += Number(log.calories || 0);
  });

  exerciseLogs.forEach((log) => {
    ensureDay(normalizeDate(log.date)).caloriesBurned += Number(log.calories_burned || 0);
  });

  sleepLogs.forEach((log) => {
    const entry = ensureDay(normalizeDate(log.date));
    entry.sleepHours += Number(log.hours || 0);
    entry.sleepCount += 1;
  });

  weightLogs.forEach((log) => {
    ensureDay(normalizeDate(log.date)).weight = Number(log.weight_kg || 0);
  });

  return Array.from(days.values())
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .map((day) => ({
      ...day,
      sleepHours: day.sleepCount ? day.sleepHours / day.sleepCount : 0,
      netCalories: day.caloriesIn - day.caloriesBurned,
    }));
}

function calculateRecommendations(summary, predictedSlope, clusterName) {
  const recommendations = [];

  if (summary.todayNet > 250) {
    recommendations.push({ text: "Your calorie intake is above calories burned today. Reduce portions or add movement.", type: "food" });
  }

  if (summary.avgSleep < 7) {
    recommendations.push({ text: "Average sleep is below 7 hours. Aim for a consistent bedtime and recovery window.", type: "sleep" });
  }

  if (summary.weeklyExerciseMinutes < 150) {
    recommendations.push({ text: "Try to reach at least 150 minutes of exercise per week.", type: "exercise" });
  }

  if (predictedSlope > 0.03) {
    recommendations.push({ text: "Weight trend is rising. A small calorie deficit and regular workouts may help.", type: "trend" });
  }

  if (clusterName === "Needs Attention") {
    recommendations.push({ text: "Recent pattern suggests focusing on food quality, movement, and recovery.", type: "warning" });
  } else if (clusterName === "Balanced") {
    recommendations.push({ text: "Your recent pattern looks balanced. Keep tracking consistently.", type: "info" });
  } else if (clusterName === "Active") {
    recommendations.push({ text: "You are staying active. Maintain protein intake and recovery to keep progress steady.", type: "exercise" });
  }

  if (!recommendations.length) {
    recommendations.push({ text: "Keep logging regularly to improve the accuracy of your insights and predictions.", type: "info" });
  }

  return recommendations;
}

function updateMetric(elementId, value, suffix = "") {
  const element = document.getElementById(elementId);
  if (element) element.textContent = `${round(value, 1)}${suffix}`;
}

export async function initDashboard() {
  const currentUser = await getCurrentUser();
  if (!currentUser) {
    window.location.href = "/login";
    return;
  }

  const title = document.getElementById("dashboardUserName");
  if (title) title.textContent = currentUser.username;

  const status = document.getElementById("dashboardStatus");
  const updatedAt = document.getElementById("dashboardUpdatedAt");

  let calorieChart = null;
  let trendChart = null;

  const render = async () => {
    try {
      if (status) status.textContent = "Loading latest data...";

      const [foodLogs, exerciseLogs] = await Promise.all([
        fetchJson("/api/foods/food_logs").catch(() => []),
        fetchJson("/api/exercises/exercise_logs").catch(() => []),
      ]);

      const today = normalizeDate(new Date());
      const todayFoods = (foodLogs || []).filter((log) => normalizeDate(log.date) === today);
      const todayExercises = (exerciseLogs || []).filter((log) => normalizeDate(log.date) === today);

      const todayCaloriesIn = todayFoods.reduce((acc, log) => acc + Number(log.calories || 0), 0);
      const todayCaloriesBurned = todayExercises.reduce((acc, log) => acc + Number(log.calories_burned || 0), 0);
      const todayNet = todayCaloriesIn - todayCaloriesBurned;

      updateMetric("todayCaloriesIn", todayCaloriesIn);
      updateMetric("todayCaloriesBurned", todayCaloriesBurned);
      updateMetric("todayNetCalories", todayNet);

      const [sleepLogs, weightLogs] = await Promise.all([
        fetchJson("/api/sleeps/sleep_logs").catch(() => []),
        fetchJson("/api/weights/weight_logs").catch(() => []),
      ]);

      const series = buildDailySeries(foodLogs || [], exerciseLogs || [], sleepLogs || [], weightLogs || []);
      const recent = series.slice(-7);

      if (calorieChart) calorieChart.destroy();
      const calorieCtx = document.getElementById("calorieComparisonChart");
      if (calorieCtx) {
        calorieChart = new Chart(calorieCtx, {
          type: "bar",
          data: {
            labels: ["Today"],
            datasets: [
              {
                label: "Calories In",
                data: [todayCaloriesIn],
                backgroundColor: "rgba(59, 130, 246, 0.85)",
              },
              {
                label: "Calories Burned",
                data: [todayCaloriesBurned],
                backgroundColor: "rgba(16, 185, 129, 0.85)",
              },
            ],
          },
          options: {
            responsive: true,
            plugins: { legend: { position: "bottom" } },
            scales: { y: { beginAtZero: true } },
          },
        });
      }

      if (trendChart) trendChart.destroy();
      const trendCtx = document.getElementById("dailyTrendChart");
      if (trendCtx) {
        const chartLabels = recent.length ? recent.map((entry) => formatDate(entry.date)) : ["No data yet"];
        const intakeSeries = recent.length ? recent.map((entry) => round(entry.caloriesIn, 1)) : [0];
        const burnSeries = recent.length ? recent.map((entry) => round(entry.caloriesBurned, 1)) : [0];

        trendChart = new Chart(trendCtx, {
          type: "line",
          data: {
            labels: chartLabels,
            datasets: [
              {
                label: "Calories In",
                data: intakeSeries,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                tension: 0.3,
              },
              {
                label: "Calories Burned",
                data: burnSeries,
                borderColor: "#10b981",
                backgroundColor: "rgba(16, 185, 129, 0.15)",
                tension: 0.3,
              },
            ],
          },
          options: {
            responsive: true,
            plugins: { legend: { position: "bottom" } },
          },
        });
      }

      if (status) status.textContent = "Live health snapshot updated.";
      if (updatedAt) updatedAt.textContent = new Date().toLocaleTimeString();
    } catch (error) {
      if (status) status.textContent = error.message || "Unable to load dashboard data.";
    }
  };

  await render();
  setInterval(render, 30000);
}

export async function initAnalytics() {
  const currentUser = await getCurrentUser();
  if (!currentUser) {
    window.location.href = "/login";
    return;
  }

  const title = document.getElementById("analyticsUserName");
  if (title) title.textContent = currentUser.username;

  const [foodLogs, exerciseLogs, sleepLogs, weightLogs] = await Promise.all([
    fetchJson("/api/foods/food_logs").catch(() => []),
    fetchJson("/api/exercises/exercise_logs").catch(() => []),
    fetchJson("/api/sleeps/sleep_logs").catch(() => []),
    fetchJson("/api/weights/weight_logs").catch(() => []),
  ]);

  const dailySeries = buildDailySeries(foodLogs, exerciseLogs, sleepLogs, weightLogs);
  const currentWeight = weightLogs.length ? Number(weightLogs[weightLogs.length - 1].weight_kg) : Number(currentUser.weight_kg || 0);
  const currentHeightMeters = Number(currentUser.height_cm || 0) / 100;
  const bmi = currentHeightMeters > 0 ? currentWeight / (currentHeightMeters ** 2) : 0;

  updateMetric("currentBmi", bmi);
  // If height not provided, prompt user to add height in profile instead of showing 0
  const bmiEl = document.getElementById("currentBmi");
  if (!currentHeightMeters || currentHeightMeters <= 0) {
    if (bmiEl) bmiEl.textContent = "Add height in profile";
  } else {
    updateMetric("currentBmi", bmi);
  }

  updateMetric("avgSleepHours", dailySeries.reduce((acc, day) => acc + day.sleepHours, 0) / Math.max(dailySeries.length, 1));
  updateMetric("avgCalorieBalance", dailySeries.reduce((acc, day) => acc + day.netCalories, 0) / Math.max(dailySeries.length, 1));

  const weightPoints = weightLogs
    .slice()
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .map((log, index, array) => ({
      x: (new Date(log.date) - new Date(array[0].date)) / 86400000,
      y: Number(log.weight_kg),
    }));

  const regression = weightPoints.length
    ? linearRegression(weightPoints)
    : { slope: 0, intercept: currentWeight || Number(currentUser.weight_kg || 0) };

  const lastX = weightPoints.length ? weightPoints[weightPoints.length - 1].x : 0;
  const predictedWeights = Array.from({ length: 7 }, (_, index) => {
    const dayX = lastX + index + 1;
    return {
      day: index + 1,
      weight: round(regression.slope * dayX + regression.intercept, 2),
    };
  });

  const weightPredictionEl = document.getElementById("weightPredictionText");
  if (weightPredictionEl) {
    if (weightLogs.length === 0) {
      weightPredictionEl.textContent = "Add weight logs to make the prediction trend more accurate. Using your current profile weight as a baseline.";
    } else {
      weightPredictionEl.textContent = `Estimated weight in 7 days: ${predictedWeights[predictedWeights.length - 1].weight} kg. This forecast is based on your recent recorded weight trend.`;
    }
  }

  const weightChartCtx = document.getElementById("weightPredictionChart");
  if (weightChartCtx && weightLogs.length > 0) {
    const labels = weightLogs
      .slice()
      .sort((a, b) => new Date(a.date) - new Date(b.date))
      .map((log) => formatDate(log.date));

    const forecastLabels = predictedWeights.map((entry) => `Day +${entry.day}`);
    new Chart(weightChartCtx, {
      type: "line",
      data: {
        labels: [...labels, ...forecastLabels],
        datasets: [
          {
            label: "Actual Weight",
            data: [
              ...weightLogs.slice().sort((a, b) => new Date(a.date) - new Date(b.date)).map((log) => Number(log.weight_kg)),
              ...Array(predictedWeights.length).fill(null),
            ],
            borderColor: "#0f172a",
            tension: 0.25,
          },
          {
            label: "Forecast",
            data: [
              ...Array(Math.max(labels.length - 1, 0)).fill(null),
              weightLogs.length ? Number(weightLogs[weightLogs.length - 1].weight_kg) : null,
              ...predictedWeights.map((entry) => entry.weight),
            ],
            borderColor: "#8b5cf6",
            borderDash: [6, 4],
            tension: 0.25,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom" } },
      },
    });
  }

  const featureRows = dailySeries.filter((day) => day.caloriesIn || day.caloriesBurned || day.sleepHours);
  const featurePoints = featureRows.map((day) => [day.caloriesIn, day.caloriesBurned, day.sleepHours, day.netCalories]);
  let clusterName = "Balanced";
  let clusterDescription = "You are maintaining a balanced recent pattern.";

  if (featurePoints.length >= 2) {
    const { centroids, labels } = kMeans(featurePoints, 3);
    const latestIndex = labels.length - 1;
    const latestCentroid = centroids[labels[latestIndex]] || centroids[0];
    clusterName = labelCluster(latestCentroid);

    if (clusterName === "Needs Attention") {
      clusterDescription = "Recent logs suggest high intake relative to activity or lower sleep recovery.";
    } else if (clusterName === "Active") {
      clusterDescription = "Recent logs show stronger activity levels and better balance.";
    } else {
      clusterDescription = "Recent logs are generally stable and reasonably balanced.";
    }
  } else if (featurePoints.length === 1) {
    const onlyDay = featurePoints[0];
    clusterName = labelCluster(onlyDay);
    clusterDescription = "Add more daily logs to make clustering more accurate.";
  }

  const clusterNameEl = document.getElementById("healthCategoryName");
  const clusterDescriptionEl = document.getElementById("healthCategoryDescription");
  if (clusterNameEl) clusterNameEl.textContent = clusterName;
  if (clusterDescriptionEl) clusterDescriptionEl.textContent = clusterDescription;

  const summary = {
    todayNet: dailySeries.length ? dailySeries[dailySeries.length - 1].netCalories : 0,
    avgSleep: dailySeries.reduce((acc, day) => acc + day.sleepHours, 0) / Math.max(dailySeries.length, 1),
    weeklyExerciseMinutes: exerciseLogs
      .filter((log) => {
        const logDate = new Date(log.date);
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - 7);
        return logDate >= cutoff;
      })
      .reduce((acc, log) => acc + Number(log.duration_min || 0), 0),
  };

  const recommendations = calculateRecommendations(summary, regression.slope, clusterName);
  const recommendationsList = document.getElementById("recommendationsList");
  if (recommendationsList) {
    const iconFor = (type) => {
      switch (type) {
        case "food":
          return { cls: "bi-basket3 rec-icon-food" };
        case "sleep":
          return { cls: "bi-moon-stars rec-icon-sleep" };
        case "exercise":
          return { cls: "bi-heart-pulse rec-icon-exercise" };
        case "trend":
          return { cls: "bi-graph-up rec-icon-trend" };
        case "warning":
          return { cls: "bi-exclamation-triangle rec-icon-food" };
        default:
          return { cls: "bi-info-circle rec-icon-info" };
      }
    };

    recommendationsList.innerHTML = recommendations
      .map((item) => {
        const icon = iconFor(item.type || "info");
        return `<li><i class="bi ${icon.cls}"></i><div class="rec-text">${item.text}</div></li>`;
      })
      .join("");
  }
}