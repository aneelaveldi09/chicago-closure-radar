"use client"

import { useEffect, useMemo, useState } from "react"
import { cn } from "@/lib/utils"

type Grid = { rows: number; cols: number }

const DEFAULT_GRIDS: Record<string, Grid> = {
  "6x4": { rows: 4, cols: 6 },
  "8x8": { rows: 8, cols: 8 },
  "8x3": { rows: 3, cols: 8 },
  "4x6": { rows: 6, cols: 4 },
  "3x8": { rows: 8, cols: 3 },
}

type PredefinedGridKey = keyof typeof DEFAULT_GRIDS

interface PixelImageProps {
  src: string
  alt?: string
  grid?: PredefinedGridKey
  customGrid?: Grid
  grayscaleAnimation?: boolean
  pixelFadeInDuration?: number
  maxAnimationDelay?: number
  colorRevealDelay?: number
  className?: string
}

export const PixelImage = ({
  src,
  alt = "Image",
  grid = "6x4",
  grayscaleAnimation = true,
  pixelFadeInDuration = 1000,
  maxAnimationDelay = 1200,
  colorRevealDelay = 1300,
  customGrid,
  className,
}: PixelImageProps) => {
  const [isVisible, setIsVisible] = useState(false)
  const [showColor, setShowColor] = useState(false)

  const { rows, cols } = useMemo(() => {
    const isValidGrid = (g?: Grid) => {
      if (!g) return false
      return Number.isInteger(g.rows) && Number.isInteger(g.cols) &&
        g.rows >= 1 && g.cols >= 1 && g.rows <= 16 && g.cols <= 16
    }
    return isValidGrid(customGrid) ? customGrid! : DEFAULT_GRIDS[grid]
  }, [customGrid, grid])

  useEffect(() => {
    setIsVisible(true)
    const t = setTimeout(() => setShowColor(true), colorRevealDelay)
    return () => clearTimeout(t)
  }, [colorRevealDelay])

  const pieces = useMemo(() => {
    return Array.from({ length: rows * cols }, (_, index) => {
      const row = Math.floor(index / cols)
      const col = index % cols
      const clipPath = `polygon(
        ${col * (100 / cols)}% ${row * (100 / rows)}%,
        ${(col + 1) * (100 / cols)}% ${row * (100 / rows)}%,
        ${(col + 1) * (100 / cols)}% ${(row + 1) * (100 / rows)}%,
        ${col * (100 / cols)}% ${(row + 1) * (100 / rows)}%
      )`
      return { clipPath, delay: Math.random() * maxAnimationDelay }
    })
  }, [rows, cols, maxAnimationDelay])

  return (
    <div className={cn("relative select-none", className)}>
      {pieces.map((piece, index) => (
        <div
          key={index}
          className={cn("absolute inset-0 transition-all ease-out", isVisible ? "opacity-100" : "opacity-0")}
          style={{
            clipPath: piece.clipPath,
            transitionDelay: `${piece.delay}ms`,
            transitionDuration: `${pixelFadeInDuration}ms`,
          }}
        >
          <img
            src={src}
            alt={index === 0 ? alt : ""}
            className={cn(
              "w-full h-full object-cover",
              grayscaleAnimation && (showColor ? "grayscale-0" : "grayscale"),
              "transition-[filter]"
            )}
            style={{
              transitionDuration: grayscaleAnimation ? `${pixelFadeInDuration}ms` : "0ms",
            }}
            draggable={false}
          />
        </div>
      ))}
    </div>
  )
}
