"use client";

import { cn } from "@/lib/utils";
import React, { useEffect, useState } from "react";
import { GlowingEffect } from "./glowing-effect";

export const InfiniteMovingCards = ({
  items,
  direction = "left",
  speed = "fast",
  pauseOnHover = true,
  className,
  cardClassName,
}: {
  items: {
    quote: string;
    name: string;
    title: string;
    image?: string;
  }[];
  direction?: "left" | "right";
  speed?: "fast" | "normal" | "slow";
  pauseOnHover?: boolean;
  className?: string;
  cardClassName?: string;
}) => {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const scrollerRef = React.useRef<HTMLUListElement>(null);

  useEffect(() => {
    addAnimation();
  }, []);
  const [start, setStart] = useState(false);
  function addAnimation() {
    if (containerRef.current && scrollerRef.current) {
      const scrollerContent = Array.from(scrollerRef.current.children);

      scrollerContent.forEach((item) => {
        const duplicatedItem = item.cloneNode(true);
        if (scrollerRef.current) {
          scrollerRef.current.appendChild(duplicatedItem);
        }
      });

      getDirection();
      getSpeed();
      setStart(true);
    }
  }
  const getDirection = () => {
    if (containerRef.current) {
      if (direction === "left") {
        containerRef.current.style.setProperty(
          "--animation-direction",
          "forwards",
        );
      } else {
        containerRef.current.style.setProperty(
          "--animation-direction",
          "reverse",
        );
      }
    }
  };
  const getSpeed = () => {
    if (containerRef.current) {
      if (speed === "fast") {
        containerRef.current.style.setProperty("--animation-duration", "20s");
      } else if (speed === "normal") {
        containerRef.current.style.setProperty("--animation-duration", "40s");
      } else {
        containerRef.current.style.setProperty("--animation-duration", "80s");
      }
    }
  };
  return (
    <div
      ref={containerRef}
      className={cn(
        "scroller relative z-20 max-w-7xl overflow-hidden [mask-image:linear-gradient(to_right,transparent,white_20%,white_80%,transparent)]",
        className,
      )}
    >
      <ul
        ref={scrollerRef}
        className={cn(
          "flex w-max min-w-full shrink-0 flex-nowrap gap-4 py-4",
          start && "animate-scroll",
          pauseOnHover && "hover:[animation-play-state:paused]",
        )}
      >
        {items.map((item, idx) => (
          <li
            className={cn(
              "relative shrink-0 rounded-2xl bg-white/10 backdrop-blur-sm overflow-hidden flex flex-col",
              cardClassName || "w-[350px] max-w-full px-8 py-6 md:w-[450px]"
            )}
            key={item.name || item.quote || idx}
          >
            <GlowingEffect
              disabled={false}
              variant="white"
              glow={true}
              spread={20}
              blur={8}
              proximity={100}
              borderWidth={1}
            />
            {item.image ? (
              <img
                src={item.image}
                alt={item.quote || "Card image"}
                className="w-full h-full object-cover"
                style={{ width: "100%", height: "100%" }}
              />
            ) : (
              <blockquote className={cardClassName ? "px-0 flex flex-col" : "px-8 py-6 flex flex-col"}>
                <div
                  aria-hidden="true"
                  className="user-select-none pointer-events-none absolute -top-0.5 -left-0.5 -z-1 h-[calc(100%_+_4px)] w-[calc(100%_+_4px)]"
                ></div>
                <span className="relative z-20 text-lg leading-[1.6] font-normal text-white">
                  {item.quote}
                </span>
                {(item.name || item.title) && (
                  <div className="relative z-20 mt-6 flex flex-row items-center">
                    <span className="flex flex-col gap-1">
                      {item.name && (
                        <span className="text-base leading-[1.6] font-normal text-white/90">
                          {item.name}
                        </span>
                      )}
                      {item.title && (
                        <span className="text-base leading-[1.6] font-normal text-white/80">
                          {item.title}
                        </span>
                      )}
                    </span>
                  </div>
                )}
              </blockquote>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};
