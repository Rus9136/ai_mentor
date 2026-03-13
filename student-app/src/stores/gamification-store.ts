import { create } from 'zustand';

interface XpToastData {
  amount: number;
  levelUp?: number;
}

interface GamificationStore {
  prevXp: number;
  setPrevXp: (xp: number) => void;
  xpToast: XpToastData | null;
  showXpToast: (amount: number, levelUp?: number) => void;
  hideXpToast: () => void;
  seenAchievementIds: Set<number>;
  markAchievementSeen: (id: number) => void;
}

export const useGamificationStore = create<GamificationStore>((set) => ({
  prevXp: 0,
  setPrevXp: (xp) => set({ prevXp: xp }),
  xpToast: null,
  showXpToast: (amount, levelUp) => set({ xpToast: { amount, levelUp } }),
  hideXpToast: () => set({ xpToast: null }),
  seenAchievementIds: new Set(),
  markAchievementSeen: (id) =>
    set((state) => ({
      seenAchievementIds: new Set([...state.seenAchievementIds, id]),
    })),
}));
