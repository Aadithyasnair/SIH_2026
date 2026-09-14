"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { Alert, getRisk, isDarknetOrTor } from "@/lib/data";
import { NetworkEvent } from "@/lib/api";

export const countryCoordinates: Record<string, { lat: number; lng: number; name: string }> = {
  US: { lat: 37.09, lng: -95.71, name: "United States" },
  USA: { lat: 37.09, lng: -95.71, name: "United States" },
  "United States": { lat: 37.09, lng: -95.71, name: "United States" },
  DE: { lat: 51.16, lng: 10.45, name: "Germany" },
  Germany: { lat: 51.16, lng: 10.45, name: "Germany" },
  NL: { lat: 52.13, lng: 5.29, name: "Netherlands" },
  Netherlands: { lat: 52.13, lng: 5.29, name: "Netherlands" },
  SE: { lat: 60.12, lng: 18.64, name: "Sweden" },
  Sweden: { lat: 60.12, lng: 18.64, name: "Sweden" },
  CH: { lat: 46.81, lng: 8.22, name: "Switzerland" },
  Switzerland: { lat: 46.81, lng: 8.22, name: "Switzerland" },
  JP: { lat: 36.20, lng: 138.25, name: "Japan" },
  Japan: { lat: 36.20, lng: 138.25, name: "Japan" },
  GB: { lat: 55.37, lng: -3.43, name: "United Kingdom" },
  UK: { lat: 55.37, lng: -3.43, name: "United Kingdom" },
  "United Kingdom": { lat: 55.37, lng: -3.43, name: "United Kingdom" },
  SG: { lat: 1.35, lng: 103.81, name: "Singapore" },
  Singapore: { lat: 1.35, lng: 103.81, name: "Singapore" },
  RO: { lat: 45.94, lng: 24.96, name: "Romania" },
  Romania: { lat: 45.94, lng: 24.96, name: "Romania" },
  NG: { lat: 9.08, lng: 8.67, name: "Nigeria" },
  Nigeria: { lat: 9.08, lng: 8.67, name: "Nigeria" },
  PA: { lat: 8.53, lng: -80.78, name: "Panama" },
  Panama: { lat: 8.53, lng: -80.78, name: "Panama" },
  CY: { lat: 35.12, lng: 33.42, name: "Cyprus" },
  Cyprus: { lat: 35.12, lng: 33.42, name: "Cyprus" },
  RU: { lat: 61.52, lng: 105.31, name: "Russia" },
  Russia: { lat: 61.52, lng: 105.31, name: "Russia" },
  "Russian Federation": { lat: 61.52, lng: 105.31, name: "Russian Federation" },
  IN: { lat: 20.59, lng: 78.96, name: "India" },
  India: { lat: 20.59, lng: 78.96, name: "India" },
  CA: { lat: 56.13, lng: -106.34, name: "Canada" },
  Canada: { lat: 56.13, lng: -106.34, name: "Canada" },
  BR: { lat: -14.23, lng: -51.92, name: "Brazil" },
  Brazil: { lat: -14.23, lng: -51.92, name: "Brazil" },
  FR: { lat: 46.22, lng: 2.21, name: "France" },
  France: { lat: 46.22, lng: 2.21, name: "France" },
  CN: { lat: 35.86, lng: 104.19, name: "China" },
  China: { lat: 35.86, lng: 104.19, name: "China" },
  AU: { lat: -25.27, lng: 133.77, name: "Australia" },
  Australia: { lat: -25.27, lng: 133.77, name: "Australia" },
};

const locations = [
  { name: "USA", lat: 37.09, lng: -95.71 },
  { name: "Canada", lat: 56.13, lng: -106.34 },
  { name: "Germany", lat: 51.16, lng: 10.45 },
  { name: "Netherlands", lat: 52.13, lng: 5.29 },
  { name: "Nigeria", lat: 9.08, lng: 8.67 },
  { name: "Singapore", lat: 1.35, lng: 103.81 },
  { name: "Panama", lat: 8.53, lng: -80.78 },
  { name: "Switzerland", lat: 46.81, lng: 8.22 },
  { name: "Cyprus", lat: 35.12, lng: 33.42 },
  { name: "Russia", lat: 61.52, lng: 105.31 },
  { name: "India", lat: 20.59, lng: 78.96 },
  { name: "Japan", lat: 36.20, lng: 138.25 },
  { name: "Brazil", lat: -14.23, lng: -51.92 },
  { name: "Sweden", lat: 60.12, lng: 18.64 },
  { name: "Romania", lat: 45.94, lng: 24.96 },
  { name: "United Kingdom", lat: 55.37, lng: -3.43 },
];

export function extractCountriesFromText(text: string): { lat: number; lng: number; name: string }[] {
  if (!text) return [];
  const found: { lat: number; lng: number; name: string }[] = [];
  const checked = new Set<string>();

  // Check country names / keys against text
  for (const [key, coords] of Object.entries(countryCoordinates)) {
    if (key.length < 3) continue; // skip 2-letter codes for broad text regex to prevent false positives
    const regex = new RegExp(`\\b${key}\\b`, "i");
    if (regex.test(text) && !checked.has(coords.name)) {
      checked.add(coords.name);
      found.push(coords);
    }
  }

  // Check 2-letter codes if prefixed or delimited (e.g., US, DE, NL)
  for (const [key, coords] of Object.entries(countryCoordinates)) {
    if (key.length === 2) {
      const codeRegex = new RegExp(`\\b${key}\\b`);
      if (codeRegex.test(text) && !checked.has(coords.name)) {
        checked.add(coords.name);
        found.push(coords);
      }
    }
  }

  return found;
}

/*
 * Your Earth texture is shifted approximately
 * 20 degrees east.
 *
 * Therefore the geographic longitude must be
 * shifted 20 degrees west before converting it
 * to the Three.js sphere coordinate.
 */
const TEXTURE_LONGITUDE_OFFSET = 20;

/* =====================================================
   LATITUDE / LONGITUDE → THREE.JS POSITION
   ===================================================== */

function pointOnGlobe(
  lat: number,
  lng: number,
  radius = 1.035
) {
  /*
   * Correct the longitude to match the
   * actual Earth texture.
   */
  const mappedLng =
    lng - TEXTURE_LONGITUDE_OFFSET;

  const latRad =
    THREE.MathUtils.degToRad(lat);

  const lngRad =
    THREE.MathUtils.degToRad(mappedLng);

  /*
   * This matches the UV orientation of
   * THREE.SphereGeometry.
   */
  return new THREE.Vector3(
    radius *
      Math.cos(latRad) *
      Math.cos(lngRad),

    radius *
      Math.sin(latRad),

    -radius *
      Math.cos(latRad) *
      Math.sin(lngRad)
  );
}

/* =====================================================
   COUNTRY LABEL
   ===================================================== */

function textSprite(text: string) {
  const canvas =
    document.createElement("canvas");

  canvas.width = 512;
  canvas.height = 128;

  const context =
    canvas.getContext("2d")!;

  context.clearRect(
    0,
    0,
    canvas.width,
    canvas.height
  );

  context.font =
    "700 38px Inter, Arial";

  context.textAlign =
    "center";

  context.textBaseline =
    "middle";

  /* Text outline */
  context.lineWidth = 8;

  context.strokeStyle =
    "#031226";

  context.strokeText(
    text,
    canvas.width / 2,
    canvas.height / 2
  );

  /* Text */
  context.fillStyle =
    "#ffffff";

  context.fillText(
    text,
    canvas.width / 2,
    canvas.height / 2
  );

  const texture =
    new THREE.CanvasTexture(canvas);

  texture.colorSpace =
    THREE.SRGBColorSpace;

  const material =
    new THREE.SpriteMaterial({
      map: texture,

      transparent: true,

      /*
       * IMPORTANT:
       * The Earth can hide labels that
       * are on the back of the globe.
       */
      depthTest: true,
      depthWrite: false,
    });

  const sprite =
    new THREE.Sprite(material);

  /*
   * Bottom-center of label attaches
   * to the geographic position.
   */
  sprite.center.set(
    0.5,
    0
  );

  sprite.scale.set(
    0.42,
    0.105,
    1
  );

  return sprite;
}

/* =====================================================
   COUNTRY GLOBE
   ===================================================== */

export function CountryGlobe({
  alerts,
  playing,
  speed,
  liveEvents = [],
}: {
  alerts: Alert[];
  playing: boolean;
  speed: number;
  liveEvents?: NetworkEvent[];
}) {
  const host =
    useRef<HTMLDivElement>(null);

  const live =
    useRef(playing);

  const rate =
    useRef(speed);

  const liveGroupRef =
    useRef<THREE.Group | null>(null);

  const alertGroupRef =
    useRef<THREE.Group | null>(null);

  live.current =
    playing;

  rate.current =
    speed;

  useEffect(() => {
    const element =
      host.current;

    if (!element) return;

    /* =================================================
       SCENE
       ================================================= */

    const scene =
      new THREE.Scene();

    /* =================================================
       CAMERA
       ================================================= */

    const camera =
      new THREE.PerspectiveCamera(
        38,
        1,
        0.1,
        100
      );

    camera.position.set(
      0,
      0.08,
      3.25
    );

    /* =================================================
       RENDERER
       ================================================= */

    const renderer =
      new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
      });

    renderer.setPixelRatio(
      Math.min(
        window.devicePixelRatio,
        2
      )
    );

    element.appendChild(
      renderer.domElement
    );

    /* =================================================
       GLOBE
       ================================================= */

    const globe =
      new THREE.Group();

    /*
     * Initial rotation only.
     * This does NOT affect the geographic
     * coordinate calculation.
     */
    globe.rotation.y =
      -0.38;

    const alertGroup =
      new THREE.Group();
    globe.add(alertGroup);
    alertGroupRef.current =
      alertGroup;

    const liveGroup =
      new THREE.Group();
    globe.add(liveGroup);
    liveGroupRef.current =
      liveGroup;

    scene.add(globe);

    /* =================================================
       EARTH TEXTURE
       ================================================= */

    const texture =
      new THREE.TextureLoader().load(
        "/assets/earth-equirectangular.png"
      );

    texture.colorSpace =
      THREE.SRGBColorSpace;

    /* =================================================
       EARTH
       ================================================= */

    const earth =
      new THREE.Mesh(
        new THREE.SphereGeometry(
          1,
          96,
          64
        ),

        new THREE.MeshPhongMaterial({
          map: texture,

          shininess: 12,

          specular:
            new THREE.Color(
              "#1b6da3"
            ),
        })
      );

    globe.add(earth);

    /* =================================================
       GLOW
       ================================================= */

    const glow =
      new THREE.Mesh(
        new THREE.SphereGeometry(
          1.025,
          96,
          64
        ),

        new THREE.MeshBasicMaterial({
          color:
            "#28c9ff",

          transparent:
            true,

          opacity:
            0.10,

          side:
            THREE.BackSide,
        })
      );

    globe.add(glow);

    /* =================================================
       LIGHTING
       ================================================= */

    scene.add(
      new THREE.AmbientLight(
        "#9edcff",
        1.5
      )
    );

    const light =
      new THREE.DirectionalLight(
        "#71d7ff",
        1.6
      );

    light.position.set(
      3,
      2,
      4
    );

    scene.add(light);

    /* =================================================
       COUNTRY MARKERS + LABELS
       ================================================= */

    locations.forEach(
      (location, index) => {

        /*
         * ---------------------------------------------
         * MARKER POSITION
         * ---------------------------------------------
         *
         * Both marker and label use exactly the
         * same corrected geographic position.
         */

        const markerPosition =
          pointOnGlobe(
            location.lat,
            location.lng,
            1.035
          );

        /* ---------------------------------------------
           MARKER
           --------------------------------------------- */

        const marker =
          new THREE.Mesh(
            new THREE.SphereGeometry(
              index < 3
                ? 0.03
                : 0.022,

              16,
              16
            ),

            new THREE.MeshBasicMaterial({
              color:
                index < 3
                  ? "#ff5267"
                  : "#53f5a0",
            })
          );

        marker.position.copy(
          markerPosition
        );

        globe.add(marker);

        /* ---------------------------------------------
           LABEL
           --------------------------------------------- */

        /*
         * Slightly farther from the globe,
         * but along the SAME radial direction.
         */
        const labelPosition =
          pointOnGlobe(
            location.lat,
            location.lng,
            1.075
          );

        const label =
          textSprite(
            location.name
          );

        label.position.copy(
          labelPosition
        );

        globe.add(label);
      }
    );

    /* =================================================
       RESIZE
       ================================================= */

    const resize = () => {
      const size =
        Math.min(
          element.clientWidth,
          410
        );

      renderer.setSize(
        size,
        size,
        false
      );

      camera.aspect =
        1;

      camera.updateProjectionMatrix();
    };

    resize();

    const observer =
      new ResizeObserver(
        resize
      );

    observer.observe(
      element
    );

    /* =================================================
       DRAGGING
       ================================================= */

    let dragging =
      false;

    let lastX = 0;
    let lastY = 0;

    const down = (
      event: PointerEvent
    ) => {
      dragging = true;

      lastX =
        event.clientX;

      lastY =
        event.clientY;

      renderer.domElement.setPointerCapture(
        event.pointerId
      );
    };

    const move = (
      event: PointerEvent
    ) => {
      if (!dragging)
        return;

      globe.rotation.y +=
        (event.clientX -
          lastX) *
        0.012;

      globe.rotation.x =
        THREE.MathUtils.clamp(
          globe.rotation.x +
            (event.clientY -
              lastY) *
              0.008,

          -0.55,
          0.55
        );

      lastX =
        event.clientX;

      lastY =
        event.clientY;
    };

    const up = () => {
      dragging = false;
    };

    renderer.domElement.addEventListener(
      "pointerdown",
      down
    );

    renderer.domElement.addEventListener(
      "pointermove",
      move
    );

    renderer.domElement.addEventListener(
      "pointerup",
      up
    );

    renderer.domElement.addEventListener(
      "pointercancel",
      up
    );

    /* =================================================
       ANIMATION
       ================================================= */

    let frame = 0;

    const animate = () => {
      frame =
        requestAnimationFrame(
          animate
        );

      if (
        live.current &&
        !dragging
      ) {
        globe.rotation.y +=
          0.0028 *
          rate.current;
      }

      renderer.render(
        scene,
        camera
      );
    };

    animate();

    /* =================================================
       CLEANUP
       ================================================= */

    return () => {
      cancelAnimationFrame(
        frame
      );

      observer.disconnect();

      renderer.domElement.removeEventListener(
        "pointerdown",
        down
      );

      renderer.domElement.removeEventListener(
        "pointermove",
        move
      );

      renderer.domElement.removeEventListener(
        "pointerup",
        up
      );

      renderer.domElement.removeEventListener(
        "pointercancel",
        up
      );

      texture.dispose();

      renderer.dispose();

      element.replaceChildren();
    };
  }, []);

  /* =================================================
     DYNAMIC ALERT CONNECTIONS (UPDATED WITHOUT RELOADING GLOBE)
     ================================================= */
  useEffect(() => {
    const alertGroup = alertGroupRef.current;
    if (!alertGroup) return;

    // Clear previous alert batch
    while (alertGroup.children.length > 0) {
      const child = alertGroup.children[0] as THREE.Mesh;
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(m => m.dispose());
        } else {
          child.material.dispose();
        }
      }
      alertGroup.remove(child);
    }

    if (!alerts || alerts.length === 0) return;

    alerts.slice(0, 10).forEach((alert, index) => {
      // Extract real countries involved from the alert's geo_summary
      const countriesInAlert = extractCountriesFromText(alert.geo_summary || "");

      let fromCoord = locations[index % locations.length];
      let toCoord = locations[(index + 3) % locations.length];

      if (countriesInAlert.length >= 2) {
        fromCoord = countriesInAlert[0];
        toCoord = countriesInAlert[1];
      } else if (countriesInAlert.length === 1) {
        fromCoord = countriesInAlert[0];
        toCoord = locations[(index + 4) % locations.length];
      }

      const from = pointOnGlobe(fromCoord.lat, fromCoord.lng, 1.035);
      const to = pointOnGlobe(toCoord.lat, toCoord.lng, 1.035);
      const middle = from.clone().add(to).multiplyScalar(0.5).normalize().multiplyScalar(1.48);

      const curve = new THREE.QuadraticBezierCurve3(from, middle, to);
      const isTor = isDarknetOrTor(alert);
      const color = isTor ? "#c084fc" : getRisk(alert.risk_score).key === "high" ? "#ff5267" : "#ffc14d";

      const tube = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 30, isTor ? 0.015 : index === 0 ? 0.013 : 0.009, 6, false),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: isTor ? 0.98 : 0.92,
        })
      );

      alertGroup.add(tube);
    });
  }, [alerts]);

  /* =================================================
     DYNAMIC LIVE SIMULATION ARCS
     ================================================= */
  useEffect(() => {
    const liveGroup = liveGroupRef.current;
    if (!liveGroup) return;

    // Clear previous live batch
    while (liveGroup.children.length > 0) {
      const child = liveGroup.children[0] as THREE.Mesh;
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(m => m.dispose());
        } else {
          child.material.dispose();
        }
      }
      liveGroup.remove(child);
    }

    if (!liveEvents || liveEvents.length === 0) return;

    liveEvents.forEach((event, idx) => {
      const srcCoord = countryCoordinates[event.src_geo_country];
      const dstCoord = countryCoordinates[event.dst_geo_country];
      if (!srcCoord || !dstCoord) return;

      const from = pointOnGlobe(srcCoord.lat, srcCoord.lng, 1.04);
      const to = pointOnGlobe(dstCoord.lat, dstCoord.lng, 1.04);
      const middle = from.clone().add(to).multiplyScalar(0.5).normalize().multiplyScalar(1.52);

      const curve = new THREE.QuadraticBezierCurve3(from, middle, to);
      const isTor = isDarknetOrTor(event);
      const isAnomalous = event.event_id.includes("rapid") || event.event_id.includes("smurf");
      const color = isTor ? "#c084fc" : isAnomalous ? "#ff5267" : "#00f0ff";

      const tube = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 32, isTor ? 0.015 : isAnomalous ? 0.012 : 0.007, 6, false),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.95,
        })
      );
      liveGroup.add(tube);
    });
  }, [liveEvents]);

  return (
    <div className="globe-wrap">
      <div
        ref={host}
        className="three-globe"
      />

      <span>
        3D Earth drag to rotate
      </span>
    </div>
  );
}