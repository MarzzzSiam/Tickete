import Image from "next/image";

// A CSS viewport removes source padding without resampling or redrawing the logo.
export function Brand({ stacked = false }: { stacked?: boolean }) {
  return (
    <span className={stacked ? "brand brand-stacked" : "brand"}>
      <Image
        src={`/brand/${stacked ? "stacked" : "horizontal"}.png`}
        alt="TICKETÉ"
        width={2000}
        height={2000}
        sizes={stacked ? "180px" : "210px"}
        priority={!stacked}
      />
    </span>
  );
}
