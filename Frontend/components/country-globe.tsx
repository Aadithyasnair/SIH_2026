"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { Alert, getRisk } from "@/lib/data";

const locations = [
  { name: "USA", lat: 39, lng: -98 },
  { name: "Canada", lat: 56, lng: -106 },
  { name: "Germany", lat: 51, lng: 10 },
  { name: "Nigeria", lat: 9, lng: 8 },
  { name: "Singapore", lat: 1, lng: 104 },
  { name: "Panama", lat: 9, lng: -80 },
  { name: "Switzerland", lat: 47, lng: 8 },
  { name: "Cyprus", lat: 35, lng: 33 },
  { name: "Russia", lat: 61, lng: 90 },
  { name: "India", lat: 20, lng: 78 },
  { name: "Japan", lat: 36, lng: 138 },
  { name: "Brazil", lat: -14, lng: -51 },
];

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
}: {
  alerts: Alert[];
  playing: boolean;
  speed: number;
}) {
  const host =
    useRef<HTMLDivElement>(null);

  const live =
    useRef(playing);

  const rate =
    useRef(speed);

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
       ALERT CONNECTIONS
       ================================================= */

    alerts
      .slice(0, 3)
      .forEach(
        (alert, index) => {

          const from =
            pointOnGlobe(
              locations[index].lat,
              locations[index].lng,
              1.035
            );

          const to =
            pointOnGlobe(
              locations[index + 3].lat,
              locations[index + 3].lng,
              1.035
            );

          const middle =
            from
              .clone()
              .add(to)
              .multiplyScalar(0.5)
              .normalize()
              .multiplyScalar(1.48);

          const curve =
            new THREE.QuadraticBezierCurve3(
              from,
              middle,
              to
            );

          const color =
            getRisk(
              alert.risk_score
            ).key === "high"
              ? "#ff5267"
              : "#ffc14d";

          const tube =
            new THREE.Mesh(
              new THREE.TubeGeometry(
                curve,

                30,

                index === 0
                  ? 0.013
                  : 0.009,

                6,

                false
              ),

              new THREE.MeshBasicMaterial({
                color,

                transparent:
                  true,

                opacity:
                  0.92,
              })
            );

          globe.add(tube);
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
  }, [alerts]);

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